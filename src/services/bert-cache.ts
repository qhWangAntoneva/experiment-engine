/**
 * BERT embedding cache service — IndexedDB persistence for BERT model metadata,
 * pre-computed prototype embeddings, and text embeddings.
 *
 * Cached items are keyed by model name so switching models starts fresh.
 * All failures are non-blocking: a cache miss simply returns null, and
 * write failures log a warning and continue.
 */

// ─── Constants ───────────────────────────────────────────────────────────────

const DB_NAME = 'qca-bert-cache'
const DB_VERSION = 1
const PROTOTYPE_STORE = 'prototype-embeddings'
const TEXT_STORE = 'text-embeddings'
const MODEL_META_STORE = 'model-meta'

// ─── Interfaces ──────────────────────────────────────────────────────────────

export interface PrototypeEmbeddingEntry {
  embeddings: number[][]
  labels: number[]
  weights: number[]
}

export interface CacheStats {
  prototypeEntries: number
  textEntries: number
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

/** Fast non-crypto djb2 hash encoded as hex for text content caching. */
function hashText(text: string): string {
  let hash = 5381
  for (let i = 0; i < text.length; i++) {
    hash = ((hash << 5) + hash + text.charCodeAt(i)) | 0
  }
  return (hash >>> 0).toString(16)
}

/** Build a compound key string from model + identifier. */
function compoundKey(modelName: string, key: string): string {
  return `${modelName}::${key}`
}

// ─── BertCache ───────────────────────────────────────────────────────────────

export class BertCache {
  private db: IDBDatabase | null = null

  /**
   * Open/create the IndexedDB database. Must be called before any other method.
   * Safe to call multiple times — returns immediately if already open.
   */
  async open(): Promise<void> {
    if (this.db) return

    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION)

      request.onerror = () => {
        console.warn('BertCache: failed to open IndexedDB:', request.error)
        reject(request.error)
      }

      request.onsuccess = () => {
        this.db = request.result
        this.db.onclose = () => { this.db = null }
        resolve()
      }

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result

        if (!db.objectStoreNames.contains(PROTOTYPE_STORE)) {
          db.createObjectStore(PROTOTYPE_STORE, { keyPath: 'id' })
        }
        if (!db.objectStoreNames.contains(TEXT_STORE)) {
          db.createObjectStore(TEXT_STORE, { keyPath: 'id' })
        }
        if (!db.objectStoreNames.contains(MODEL_META_STORE)) {
          db.createObjectStore(MODEL_META_STORE, { keyPath: 'modelName' })
        }
      }
    })
  }

  /** Close the database connection. */
  close(): void {
    if (this.db) {
      this.db.close()
      this.db = null
    }
  }

  // ── Prototype embeddings ─────────────────────────────────────────────────

  /**
   * Store prototype embeddings keyed by condition_name + model_name.
   */
  async putPrototypeEmbeddings(
    modelName: string,
    conditionName: string,
    embeddings: number[][],
    labels: number[],
    weights: number[]
  ): Promise<void> {
    if (!this.db) {
      console.warn('BertCache: putPrototypeEmbeddings called before open()')
      return
    }

    const id = compoundKey(modelName, conditionName)
    const record = { id, embeddings, labels, weights, updated: Date.now() }

    return new Promise((resolve) => {
      try {
        const txn = this.db!.transaction(PROTOTYPE_STORE, 'readwrite')
        const store = txn.objectStore(PROTOTYPE_STORE)
        store.put(record)
        txn.oncomplete = () => resolve()
        txn.onerror = () => {
          console.warn('BertCache: failed to store prototype embeddings for', conditionName, txn.error)
          resolve()
        }
      } catch (e) {
        console.warn('BertCache: transaction error in putPrototypeEmbeddings:', e)
        resolve()
      }
    })
  }

  /**
   * Get prototype embeddings for a condition + model. Returns null if not cached.
   */
  async getPrototypeEmbeddings(
    modelName: string,
    conditionName: string
  ): Promise<PrototypeEmbeddingEntry | null> {
    if (!this.db) {
      console.warn('BertCache: getPrototypeEmbeddings called before open()')
      return null
    }

    const id = compoundKey(modelName, conditionName)

    return new Promise((resolve) => {
      try {
        const txn = this.db!.transaction(PROTOTYPE_STORE, 'readonly')
        const store = txn.objectStore(PROTOTYPE_STORE)
        const request = store.get(id)

        request.onsuccess = () => {
          const record = request.result
          if (record) {
            resolve({
              embeddings: record.embeddings,
              labels: record.labels,
              weights: record.weights,
            })
          } else {
            resolve(null)
          }
        }
        request.onerror = () => {
          console.warn('BertCache: failed to read prototype embeddings for', conditionName, request.error)
          resolve(null)
        }
      } catch (e) {
        console.warn('BertCache: transaction error in getPrototypeEmbeddings:', e)
        resolve(null)
      }
    })
  }

  // ── Text embeddings ──────────────────────────────────────────────────────

  /**
   * Store a single text embedding keyed by content hash + model name.
   */
  async putTextEmbedding(
    modelName: string,
    textHash: string,
    embedding: number[]
  ): Promise<void> {
    if (!this.db) {
      console.warn('BertCache: putTextEmbedding called before open()')
      return
    }

    const id = compoundKey(modelName, textHash)
    const record = { id, embedding, updated: Date.now() }

    return new Promise((resolve) => {
      try {
        const txn = this.db!.transaction(TEXT_STORE, 'readwrite')
        const store = txn.objectStore(TEXT_STORE)
        store.put(record)
        txn.oncomplete = () => resolve()
        txn.onerror = () => {
          console.warn('BertCache: failed to store text embedding for', textHash, txn.error)
          resolve()
        }
      } catch (e) {
        console.warn('BertCache: transaction error in putTextEmbedding:', e)
        resolve()
      }
    })
  }

  /**
   * Get cached text embedding. Returns null if not cached.
   */
  async getTextEmbedding(
    modelName: string,
    textHash: string
  ): Promise<number[] | null> {
    if (!this.db) {
      console.warn('BertCache: getTextEmbedding called before open()')
      return null
    }

    const id = compoundKey(modelName, textHash)

    return new Promise((resolve) => {
      try {
        const txn = this.db!.transaction(TEXT_STORE, 'readonly')
        const store = txn.objectStore(TEXT_STORE)
        const request = store.get(id)

        request.onsuccess = () => {
          const record = request.result
          resolve(record ? (record.embedding as number[]) : null)
        }
        request.onerror = () => {
          console.warn('BertCache: failed to read text embedding for', textHash, request.error)
          resolve(null)
        }
      } catch (e) {
        console.warn('BertCache: transaction error in getTextEmbedding:', e)
        resolve(null)
      }
    })
  }

  /**
   * Bulk-cache text embeddings for a batch of texts.
   *
   * Hashes for you — callers pass raw text strings.
   */
  static hashText(text: string): string {
    return hashText(text)
  }

  /**
   * Bulk-store pre-hashed text embeddings.
   */
  async putTextEmbeddingBatch(
    modelName: string,
    entries: { textHash: string; embedding: number[] }[]
  ): Promise<void> {
    if (!this.db) {
      console.warn('BertCache: putTextEmbeddingBatch called before open()')
      return
    }
    if (entries.length === 0) return

    return new Promise((resolve) => {
      try {
        const txn = this.db!.transaction(TEXT_STORE, 'readwrite')
        const store = txn.objectStore(TEXT_STORE)

        let errorOccurred = false
        for (const entry of entries) {
          const id = compoundKey(modelName, entry.textHash)
          const request = store.put({
            id,
            embedding: entry.embedding,
            updated: Date.now(),
          })
          request.onerror = () => {
            if (!errorOccurred) {
              errorOccurred = true
              console.warn('BertCache: batch put error for', entry.textHash, request.error)
            }
          }
        }

        txn.oncomplete = () => resolve()
        txn.onerror = () => {
          console.warn('BertCache: batch transaction error:', txn.error)
          resolve()
        }
      } catch (e) {
        console.warn('BertCache: transaction error in putTextEmbeddingBatch:', e)
        resolve()
      }
    })
  }

  // ── Cache management ─────────────────────────────────────────────────────

  /**
   * Clear all cached data for a specific model (e.g., when model is changed).
   */
  async clearModelCache(modelName: string): Promise<void> {
    if (!this.db) {
      console.warn('BertCache: clearModelCache called before open()')
      return
    }

    const prefix = `${modelName}::`

    await Promise.all([
      this._clearStoreByPrefix(PROTOTYPE_STORE, prefix),
      this._clearStoreByPrefix(TEXT_STORE, prefix),
    ])
  }

  /** Clear ALL cached data across all models. */
  async clearAll(): Promise<void> {
    if (!this.db) {
      console.warn('BertCache: clearAll called before open()')
      return
    }

    await Promise.all([
      this._clearStore(PROTOTYPE_STORE),
      this._clearStore(TEXT_STORE),
      this._clearStore(MODEL_META_STORE),
    ])
  }

  /** Get total cached entries count (for UI display). */
  async getCacheStats(): Promise<CacheStats> {
    if (!this.db) {
      console.warn('BertCache: getCacheStats called before open()')
      return { prototypeEntries: 0, textEntries: 0 }
    }

    const [prototypeEntries, textEntries] = await Promise.all([
      this._countStore(PROTOTYPE_STORE),
      this._countStore(TEXT_STORE),
    ])

    return { prototypeEntries, textEntries }
  }

  // ── Internal helpers ─────────────────────────────────────────────────────

  /**
   * Delete all records from a store whose key starts with the given prefix.
   */
  private _clearStoreByPrefix(storeName: string, prefix: string): Promise<void> {
    return new Promise((resolve) => {
      try {
        const txn = this.db!.transaction(storeName, 'readwrite')
        const store = txn.objectStore(storeName)
        const request = store.openCursor()

        let deleted = 0
        request.onsuccess = () => {
          const cursor = request.result
          if (cursor) {
            if (typeof cursor.key === 'string' && cursor.key.startsWith(prefix)) {
              cursor.delete()
              deleted++
            }
            cursor.continue()
          } else {
            if (deleted > 0) {
              console.info(`BertCache: cleared ${deleted} entries from ${storeName} (prefix: ${prefix})`)
            }
          }
        }
        txn.oncomplete = () => resolve()
        txn.onerror = () => {
          console.warn(`BertCache: _clearStoreByPrefix error on ${storeName}:`, txn.error)
          resolve()
        }
      } catch (e) {
        console.warn(`BertCache: _clearStoreByPrefix exception on ${storeName}:`, e)
        resolve()
      }
    })
  }

  /** Delete all records from a store. */
  private _clearStore(storeName: string): Promise<void> {
    return new Promise((resolve) => {
      try {
        const txn = this.db!.transaction(storeName, 'readwrite')
        const store = txn.objectStore(storeName)
        const request = store.clear()
        txn.oncomplete = () => resolve()
        txn.onerror = () => {
          console.warn(`BertCache: _clearStore error on ${storeName}:`, txn.error)
          resolve()
        }
      } catch (e) {
        console.warn(`BertCache: _clearStore exception on ${storeName}:`, e)
        resolve()
      }
    })
  }

  /** Count records in a store. */
  private _countStore(storeName: string): Promise<number> {
    return new Promise((resolve) => {
      try {
        const txn = this.db!.transaction(storeName, 'readonly')
        const store = txn.objectStore(storeName)
        const request = store.count()
        request.onsuccess = () => resolve(request.result)
        request.onerror = () => {
          console.warn(`BertCache: _countStore error on ${storeName}:`, request.error)
          resolve(0)
        }
      } catch (e) {
        console.warn(`BertCache: _countStore exception on ${storeName}:`, e)
        resolve(0)
      }
    })
  }
}
