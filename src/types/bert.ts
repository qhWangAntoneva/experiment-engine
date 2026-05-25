/** BERT engine status. */
export type BertModelStatus = 'unloaded' | 'loading' | 'ready' | 'error'

/** A single BERT CLS embedding vector (768-dim for bert-base-chinese). */
export type BertEmbedding = Float32Array

/** Batch of BERT embeddings returned from the worker. */
export interface BertEmbeddingBatch {
  embeddings: Float32Array[]
  modelName: string
}

/** Prototype embeddings grouped by condition, keyed by condition name. */
export interface PrototypeEmbeddingMap {
  [conditionName: string]: {
    /** One embedding vector per prototype. */
    embeddings: number[][]
    /** is_member flag for each prototype (1 = positive, 0 = negative). */
    labels: number[]
    /** Weight for each prototype (0-1). */
    weights: number[]
  }
}

/** Progress callback for BERT model loading. */
export type BertProgressCallback = (progress: number, message: string) => void

/** Request to compute embeddings for a list of texts. */
export interface ComputeEmbeddingsRequest {
  texts: string[]
  batchSize?: number
}

/** Response with computed embeddings. */
export interface ComputeEmbeddingsResponse {
  embeddings: number[][]
}

/** Fields added to PyodideWorkerRequest for BERT operations. */
export interface BertWorkerRequests {
  init_bert: { type: 'init_bert'; payload: { modelName: string } }
  compute_embeddings: { type: 'compute_embeddings'; payload: ComputeEmbeddingsRequest }
  compute_prototype_embeddings: { type: 'compute_prototype_embeddings'; payload: { prototypes: Record<string, string[]> } }
  get_bert_status: { type: 'get_bert_status' }
}

/** Fields added to PyodideWorkerResponse for BERT operations. */
export interface BertWorkerResponses {
  'bert-init-progress': { type: 'bert-init-progress'; progress: number; message: string }
  'bert-init-done': { type: 'bert-init-done'; modelName: string }
  'bert-init-error': { type: 'bert-init-error'; error: string }
  'embeddings-computed': { type: 'embeddings-computed'; embeddings: number[][] }
  'embeddings-error': { type: 'embeddings-error'; error: string }
  'prototype-embeddings-computed': { type: 'prototype-embeddings-computed'; embeddings: PrototypeEmbeddingMap }
  'bert-status': { type: 'bert-status'; loaded: boolean; modelName: string | null }
}
