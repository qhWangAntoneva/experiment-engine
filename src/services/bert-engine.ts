import { pipeline, env, type FeatureExtractionPipeline } from '@xenova/transformers'
import type {
  BertModelStatus,
  BertEmbedding,
  BertEmbeddingBatch,
  BertProgressCallback
} from '../types/bert'

/** Default BERT model for Chinese text feature extraction. */
const DEFAULT_MODEL = 'Xenova/bert-base-chinese'

/** Maximum Chinese characters before truncation.
 *  Chinese text averages ~1.5 WordPiece tokens per character for
 *  bert-base-chinese, so 380 chars ≈ 570 tokens, safely under BERT's
 *  512-token window. Transformers.js auto-truncates if still too long. */
const MAX_CHARS = 380

/** Expected hidden dimension for bert-base-chinese (used as zero-vector fallback). */
const DEFAULT_HIDDEN_DIM = 768

/**
 * In-browser BERT feature-extraction engine using Transformers.js.
 *
 * Provides CLS embedding extraction via attention-masked mean pooling
 * followed by L2 normalization. The model is lazily loaded only when
 * `loadModel()` is called, and embeddings are cached by (text, modelName)
 * to avoid redundant inference.
 */
export class BertEngine {
  private _status: BertModelStatus = 'unloaded'
  private _model: FeatureExtractionPipeline | null = null
  private _modelName: string | null = null
  private _progressCallbacks: BertProgressCallback[] = []
  private _cache: Map<string, Float32Array> = new Map()

  // ---------------------------------------------------------------------------
  // Public API
  // ---------------------------------------------------------------------------

  /** Get the current model loading status. */
  getStatus(): BertModelStatus {
    return this._status
  }

  /**
   * Register a callback to receive model-download progress updates.
   * Multiple callbacks can be registered; all are invoked on each event.
   */
  onProgress(cb: BertProgressCallback): void {
    this._progressCallbacks.push(cb)
  }

  /** True when the model is fully loaded and ready for `extractEmbeddings()`. */
  isReady(): boolean {
    return this._status === 'ready'
  }

  /** The HuggingFace model name currently loaded, or null. */
  getModelName(): string | null {
    return this._modelName
  }

  /**
   * Download and initialise the BERT feature-extraction pipeline.
   *
   * This is a long-running, network-dependent operation that reports progress
   * via any callbacks registered with `onProgress()`. Calling this method when
   * the requested model is already loaded is a no-op.  Calling it with a
   * different model name will reload the pipeline and clear the embedding cache.
   *
   * @param modelName - HuggingFace model identifier (defaults to
   *   `Xenova/bert-base-chinese`).
   * @throws If the model download or initialisation fails.
   */
  async loadModel(modelName?: string): Promise<void> {
    const name = modelName ?? DEFAULT_MODEL

    if (this._status === 'ready' && this._modelName === name) {
      return
    }

    this._status = 'loading'
    this._cache.clear()
    this._reportProgress(0, `Starting download: ${name}`)

    // Always fetch model files from HuggingFace (browser cache still applies).
    env.allowLocalModels = false
    // Prefix tag for model-version tracking in the Transformers.js local cache.
    ;(env as Record<string, unknown>).cacheKey = 'qca-bert-v1'

    try {
      this._model = await pipeline('feature-extraction', name, {
        progress_callback: (info: { progress?: number; status?: string }) => {
          const pct = info.progress ?? 0
          const msg = info.status ?? `Downloading ${name}`
          this._reportProgress(pct, msg)
        }
      })

      this._modelName = name
      this._status = 'ready'
      this._reportProgress(100, `Model ${name} loaded successfully`)
    } catch (error) {
      this._status = 'error'
      const msg = error instanceof Error ? error.message : String(error)
      this._reportProgress(0, `Failed to load ${name}: ${msg}`)
      throw new Error(`Failed to load BERT model "${name}": ${msg}`)
    }
  }

  /**
   * Extract CLS embeddings for a list of input texts.
   *
   * The pipeline performs attention-masked mean pooling over the last hidden
   * state, then each embedding is L2-normalised to unit length.  Empty or
   * whitespace-only texts produce a zero vector of `hiddenDim` length.
   *
   * Texts that have been embedded previously (same text + same model) are
   * served from an in-memory cache.  Uncached texts are processed in
   * user-configurable batches to avoid OOM on large inputs.
   *
   * @param texts   - Input strings to embed.
   * @param batchSize - Maximum texts per pipeline call (default 16).
   * @returns A batch object containing the embeddings, token counts, and model
   *   identifier.
   * @throws If the model has not been loaded yet.
   */
  async extractEmbeddings(
    texts: string[],
    batchSize: number = 16
  ): Promise<BertEmbeddingBatch> {
    if (!this._model || !this._modelName) {
      throw new Error('BERT model not loaded. Call loadModel() first.')
    }

    const embeddings: Float32Array[] = new Array(texts.length)

    // --------------- separate cached vs uncached ---------------
    const uncached: { text: string; index: number }[] = []

    for (let i = 0; i < texts.length; i++) {
      const text = texts[i]

      if (!text || text.trim().length === 0) {
        embeddings[i] = new Float32Array(DEFAULT_HIDDEN_DIM)
        continue
      }

      const cacheKey = this._makeCacheKey(text)
      const cached = this._cache.get(cacheKey)
      if (cached) {
        embeddings[i] = cached
        continue
      }

      uncached.push({ text, index: i })
    }

    if (uncached.length === 0) {
      return { embeddings, modelName: this._modelName }
    }

    // --------------- batch-inference loop ---------------
    for (let i = 0; i < uncached.length; i += batchSize) {
      const slice = uncached.slice(i, i + batchSize)
      const batchTexts = slice.map((s) => this._truncateText(s.text))

      const output = await this._model(batchTexts, {
        pooling: 'mean',
        normalize: false
      })

      // With pooling='mean', the pipeline returns Tensor[] where each Tensor
      // has shape [hiddenDim].  A single-item batch returns a bare Tensor.
      // Transformers.js types data as DataArray, but at runtime it is a
      // typed array for float model outputs.
      const tensorList = Array.isArray(output) ? output : [output]

      for (let j = 0; j < slice.length; j++) {
        const { text, index } = slice[j]
        const tensor = tensorList[j]

        // Clone the underlying data so the cache owns its own buffer.
        const raw = new Float32Array(tensor.data as Float32Array)
        const normalized = this._l2Normalize(raw)

        embeddings[index] = normalized
        this._cache.set(this._makeCacheKey(text), normalized)
      }
    }

    return { embeddings, modelName: this._modelName }
  }

  // ---------------------------------------------------------------------------
  // Private helpers
  // ---------------------------------------------------------------------------

  /**
   * Build a deduplication key that combines input text with the model identity.
   * Different models produce semantically different embeddings for the same
   * text, so the model name must be part of the cache key.
   */
  private _makeCacheKey(text: string): string {
    return `${text}\0${this._modelName}`
  }

  /**
   * Coarse truncation to keep input within BERT's 512-token window.
   * Chinese characters are roughly 1 token each in bert-base-chinese's
   * WordPiece tokeniser, so a character-level cut is a safe over-estimate.
   */
  private _truncateText(text: string): string {
    if (text.length <= MAX_CHARS) return text
    return text.slice(0, MAX_CHARS)
  }

  /**
   * L2-normalise a vector in-place and return the same reference.
   *
   * If the vector has near-zero magnitude (e.g. the model returned all zeros
   * for a degenerate input), no scaling is applied.
   */
  private _l2Normalize(vec: Float32Array): Float32Array {
    let sumSq = 0
    for (let i = 0; i < vec.length; i++) {
      sumSq += vec[i] * vec[i]
    }
    const norm = Math.sqrt(sumSq)
    if (norm > 1e-8) {
      for (let i = 0; i < vec.length; i++) {
        vec[i] /= norm
      }
    }
    return vec
  }

  /** Broadcast a progress event to every registered callback. */
  private _reportProgress(progress: number, message: string): void {
    for (const cb of this._progressCallbacks) {
      cb(progress, message)
    }
  }
}
