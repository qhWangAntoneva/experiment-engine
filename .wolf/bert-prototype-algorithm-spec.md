# BERT Prototype Similarity Algorithm Specification

> Author: Algorithm Designer
> Date: 2026-05-25
> Status: Draft
> Scope: Replaces keyword-based `PrototypeSimilarityEngine` with BERT semantic similarity.
> Integration: Outputs raw scores fed into existing calibration strategies (Direct/Indirect/Ragin).

---

## 1. Algorithm Overview

```
INPUT:  N raw texts {T_1, ..., T_N}
        M conditions {C_1, ..., C_M}, each with prototypes
        Each prototype P is (text, is_member, weight)

STAGE 1 (pre-compute, once):  Embed all prototypes → centroid vectors
STAGE 2 (batch):              Embed all texts → text vectors
STAGE 3 (similarity):         Cosine similarity to pos/neg centroids
STAGE 4 (scoring):            Softmax formula → raw scores in [0, 1]
STAGE 5 (calibration):        Existing calibration strategies → membership ∈ [0, 1]

OUTPUT: MembershipData (n_texts × n_conditions)
```

---

## 2. Embedding Extraction

### 2.1 Mean Pooling (Recommended)

For a text T tokenized into L tokens, BERT outputs hidden states H ∈ R^(L × d) at the
last layer, where d = 768 for bert-base-chinese.

```
H = BERT_last_hidden_layer(T)          # shape: (L, d)
h = (1/L) * sum_{i=1}^{L} H[i, :]     # mean pooling, shape: (d,)
h_norm = h / ||h||_2                   # L2 normalization
```

**Why mean pooling over CLS token:**

| Property | CLS token | Mean pooling |
|----------|-----------|--------------|
| Design purpose | NSP classification | Sentence representation |
| STS benchmark performance | Weaker | Consistently better (STS-B, SICK) |
| Sentence-BERT convention | Not used | Standard approach |
| Padding sensitivity | Position 0 only, ignores padding | Attention mask excludes padding |
| Gradient attribution | Concentrated on first token | Evenly distributed |
| Vietnamese/Chinese text | Comparable | Slightly better (less position bias) |

**CLS is acceptable as a fallback** if mean pooling is not available in the ONNX graph,
but the output quality will be noticeably worse for semantic similarity tasks. If using
CLS, the model should ideally be fine-tuned on NLI/STS data (not raw MLM-pretrained).

**Attention mask handling:** When mean pooling, pad tokens must be excluded:
```
attention_mask ∈ {0, 1}^L   # 1 for real tokens, 0 for padding
h = sum(H[i,:] * attention_mask[i]) / sum(attention_mask)
```

### 2.2 Model Selection

For QCA text analysis, the model should understand Chinese semantics:

| Model | Dim | Size (ONNX quantized) | Chinese support | Recommendation |
|-------|-----|----------------------|-----------------|----------------|
| `bert-base-chinese` | 768 | ~400 MB (int8: ~100MB) | Native | Gold standard |
| `paraphrase-multilingual-MiniLM-L12-v2` | 384 | ~120 MB (int8: ~30MB) | Zero-shot | Best balance |
| `shibing624/text2vec-base-chinese` | 768 | ~400 MB | Native, CoSENT trained | Best for similarity |
| `BAAI/bge-small-zh` | 512 | ~100 MB (int8: ~25MB) | Native, RAG-optimized | Lightweight |

**Recommendation:** `shibing624/text2vec-base-chinese` for quality, `paraphrase-multilingual-MiniLM-L12-v2` (int8 quantized ONNX) for browser deployment. The CoSENT-trained models are specifically optimized for cosine similarity as a semantic metric.

---

## 3. Prototype Embedding and Aggregation

### 3.1 Centroid Aggregation (Default)

For condition C with k prototypes {(P_1, L_1, w_1), ..., (P_k, L_k, w_k)}:

```
P_pos = {P_i | L_i = 1}    # positive prototypes
P_neg = {P_i | L_i = 0}    # negative prototypes

For all P in P_pos:
    e_pos_j = BERT_mean_pool(P_j)          # embedding, shape (d,)
    e_pos_j = e_pos_j / ||e_pos_j||_2       # L2 normalize

c_pos = (1/|P_pos|) * sum(e_pos_j)         # centroid, shape (d,)
c_pos = c_pos / ||c_pos||_2                 # re-normalize

c_neg = analogously for negative prototypes
```

Each condition produces two vectors: `c_pos_C` and `c_neg_C`, both in R^d, both unit-length.

### 3.2 Weighted Centroid (Optional)

When prototype weights are provided (w_i ∈ ConceptPrototype.weight):

```
c_pos = (sum(w_j * e_pos_j) / sum(w_j))    # weighted average
c_pos = c_pos / ||c_pos||_2
```

This allows the researcher to emphasize certain prototypes as "more central" examples.

### 3.3 Max-Similarity Aggregation (Alternative)

Instead of centroids, keep individual embeddings and compute:

```
sim_pos(T, C) = max_{j: L_j=1} cosine(BERT(T), BERT(P_j))
sim_neg(T, C) = max_{j: L_j=0} cosine(BERT(T), BERT(P_j))
```

**When to use max-similarity**: If prototypes represent intentionally diverse
sub-types of the category (e.g., "strong negative affect" might include both
"anger" and "disappointment" as separate sub-types in different embedding regions).

**Why centroid is the default**: Prototype theory (Rosch 1973) defines the prototype
as a *central tendency*, not as a stored exemplar. The centroid operationalizes this.
Exemplar theory (Medin & Schaffer 1978), which uses individual stored instances, is
a different (and for QCA, less appropriate) cognitive model.

### 3.4 Centroid Quality Check

After computing centroids, compute intra-class coherence:

```
coherence_pos = mean cosine similarity among all pairs in P_pos
coherence_neg = mean cosine similarity among all pairs in P_neg
```

If `coherence_pos < 0.3`, warn the researcher that positive prototypes are too diverse
— the centroid may be a poor representation. In this case, recommend max-similarity or
splitting positive prototypes into sub-groups.

---

## 4. Cosine Similarity Computation

For text T with embedding `e_T ∈ R^d` (unit length) and condition C with centroids
`c_pos, c_neg ∈ R^d` (unit length):

```
sim_pos(T, C) = e_T · c_pos         # dot product, since both are unit vectors
sim_neg(T, C) = e_T · c_neg         # ≡ cosine similarity
```

Both values are in [-1, 1].

For batch processing (N texts), the computation is a single matrix-vector multiply:

```
E = stack([e_T1, e_T2, ..., e_TN])    # shape: (N, d), each row is unit-length
S_pos = E @ c_pos                      # shape: (N,), cosine similarities
S_neg = E @ c_neg                      # shape: (N,), cosine similarities
```

**Empirical expected ranges for Chinese text with bert-base-chinese:**
- Identical texts: cos ≈ 0.98-1.0
- Same topic/domain, different wording: cos ≈ 0.7-0.9
- Related but different topic: cos ≈ 0.3-0.7
- Unrelated: cos ≈ -0.1 to 0.4
- Opposite meaning: cos ≈ -0.3 to 0.1

(These are approximate; actual values depend on model, fine-tuning, and text domain.)

---

## 5. Cosine-to-Raw-Score Formula

This is the core algorithmic decision. The raw score must be:
1. In [0, 1] range (for compatibility with RaginCalibration which assumes [0,1] inputs)
2. Monotonic in sim_pos and anti-monotonic in sim_neg
3. 0.5 when sim_pos == sim_neg (maximum ambiguity at crossover)
4. Theoretically grounded in prototype theory

### 5.1 Primary Recommendation: Softmax with Temperature

```
raw(T, C) = exp(τ · sim_pos) / [exp(τ · sim_pos) + exp(τ · sim_neg)]     (Eq. 1)

where:
  τ = temperature parameter (default τ = 5.0)
```

**Properties:**
- `raw ∈ (0, 1)` always
- `raw → 1` as `sim_pos ≫ sim_neg` (strong positive evidence)
- `raw → 0` as `sim_pos ≪ sim_neg` (strong negative evidence)
- `raw = 0.5` when `sim_pos = sim_neg` (maximum ambiguity)
- `∂raw/∂sim_pos > 0` and `∂raw/∂sim_neg < 0` (monotonic)
- τ controls discrimination: larger τ = sharper boundary, smaller τ = softer grading

**Temperature calibration:**

| τ | Behavior | Use case |
|----|----------|----------|
| 1.0 | Very soft, most scores near 0.5 | Exploratory analysis |
| 3.0 | Moderate discrimination | General QCA analysis |
| 5.0 | Sharp discrimination (default) | Well-separated concepts |
| 10.0 | Very sharp, approximates argmax | Crisp conditions |

The temperature τ can be set per-condition. A condition with very similar prototypes
(e.g., all positive prototypes express nearly identical meaning) should use a lower τ
to avoid overfitting. A condition with diverse prototypes needs a higher τ to maintain
discriminative power.

**Theoretical justification (Prototype Theory):**

Rosch's prototype theory posits that category membership is graded based on
"family resemblance" — the more features a member shares with the prototype, the
more typical it is. In embedding space:

- `sim_pos` measures resemblance to the positive prototype
- `sim_neg` measures resemblance to the negative prototype
- The softmax computes the *relative* resemblance: "how much more like the positive
  prototype is this text than like the negative prototype?"

This is mathematically equivalent to a logistic classifier with logit = τ·(sim_pos - sim_neg):

```
raw = exp(τ·sim_pos) / (exp(τ·sim_pos) + exp(τ·sim_neg))
    = 1 / (1 + exp(-τ·(sim_pos - sim_neg)))
    = σ(τ·(sim_pos - sim_neg))                                          (Eq. 2)
```

where σ is the sigmoid function. This reveals that the softmax formula is
effectively a **sigmoid of the cosine difference**, scaled by temperature.
The cosine difference `Δ = sim_pos - sim_neg ∈ [-2, 2]` captures the net
evidence, and the sigmoid maps it to a probability-like score.

**Connection to fuzzy-set QCA:** The sigmoid/symmetric around 0.5 corresponds to
the "crossover point" in QCA calibration. The temperature τ corresponds to the
steepness of the transition from non-membership to membership. This creates a natural
bridge to Ragin's log-odds calibration.

### 5.2 Alternative: Normalized Difference

```
raw(T, C) = max(0, min(1, (sim_pos - sim_neg + 1) / 2))                (Eq. 3)
```

**Properties:**
- Maps the difference range [-2, 2] → [0, 1]
- Linear in the cosine difference
- Simpler, more transparent
- No temperature parameter to tune

**When to prefer over softmax:**
- Simplicity is paramount
- The researcher prefers direct interpretability
- Cosine differences consistently span the full [-2, 2] range

**Disadvantages vs softmax:**
- Less graded: near-ties produce 0.5, small difference produces 0.55 (not 0.51)
- No parameter to adjust discrimination sharpness
- Does not correspond to a probabilistic model

### 5.3 Option C (Instance-Based Max Similarity) — NOT Recommended

```
raw = max(0, max_{j} cos(T, P_j^pos) - max_{k} cos(T, P_k^neg))       (Eq. 4)
```

This is the current character-bigram approach translated to BERT. It is compatible
with exemplar theory but not with prototype theory. It is also more expensive
(O(k) per text per condition vs O(1) with centroids).

### 5.4 Option B (Ratio) — NOT Recommended

```
raw = sim_pos / (sim_pos + sim_neg)                                     (Eq. 5)
```

Fails when `sim_pos + sim_neg` is near zero or negative. Requires shifting
cosine into [0, 2] first, which adds complexity without benefit over softmax.

### 5.5 Recommendation Summary

| Formula | Range | Temperature | Theory alignment | Efficiency | Verdict |
|---------|-------|-------------|------------------|------------|---------|
| Softmax (Eq. 1) | (0,1) | Yes (τ) | Prototype theory | O(1) | **Primary** |
| Norm-diff (Eq. 3) | [0,1] | No | Weak | O(1) | **Fallback** |
| Max-diff (Eq. 4) | [0,1] | No | Exemplar theory | O(k) | Special cases |
| Ratio (Eq. 5) | Instable | No | None | O(1) | Avoid |

---

## 6. Edge Cases

### 6.1 No Prototypes Defined for a Condition

```
IF |P_pos| + |P_neg| = 0:
    raw = np.zeros(N)    # all zeros → calibration produces 0 or 0.05
```

Rationale: Without theoretical guidance (no prototypes), assume non-membership.

### 6.2 Only Positive Prototypes (No Negatives)

```
IF |P_pos| > 0 AND |P_neg| = 0:
    sim_pos = E @ c_pos
    raw = (sim_pos + 1) / 2     # rescale [-1, 1] → [0, 1]
```

Rationale: Without negative prototypes, membership is monotonic in positive similarity.
The linear rescaling maps "most dissimilar" (cos=-1) → 0 and "identical" (cos=1) → 1.

### 6.3 Only Negative Prototypes (No Positives)

```
IF |P_pos| = 0 AND |P_neg| > 0:
    sim_neg = E @ c_neg
    raw = 1 - (sim_neg + 1) / 2    # inverses negative similarity
      = (1 - sim_neg) / 2
```

Rationale: Membership decreases as similarity to negative prototypes increases.
"Most similar to negative" (cos=1) → 0, "least similar" (cos=-1) → 1.

### 6.4 Single Prototype

```
IF |P_pos| = 1 OR |P_neg| = 1:
    Centroid = that single prototype's embedding (no averaging needed).
    Apply Eq. 1 or Eq. 3 as usual.
```

### 6.5 Empty Text Input

```
IF text = "" OR text = whitespace only:
    e_T = zero vector
    sim_pos = 0, sim_neg = 0
    raw = 0.5    # maximum ambiguity
```

The zero vector is equidistant (cosine = 0) to all unit vectors. This correctly
places empty texts at the crossover point (membership 0.5).

### 6.6 All Prototypes Identical (Degenerate Centroids)

```
IF coherence_pos == 1.0 AND coherence_neg == 1.0:
    # All prototypes in each class are semantically identical
    # Centroid is still valid (just = any prototype's embedding)
    # But: warn researcher about redundant prototypes
```

### 6.7 Cross-Condition Prototype Overlap

```
FOR conditions C_a, C_b:
    sim_between_centroids = c_pos_a · c_pos_b
    IF sim_between_centroids > 0.95:
        WARN: "C_a and C_b positive prototypes are nearly identical.
               Conditions may not be analytically distinct."
```

---

## 7. Full Pipeline Pseudocode

```
Algorithm: BERT_PROTOTYPE_CALIBRATE

Input:
  texts: List[str]                         # N raw Chinese texts
  condition_set: ConditionSet              # M conditions with prototypes
  model: BERTModel                         # Loaded BERT/ONNX model
  temperature: float = 5.0                 # Softmax temperature
  pooling: str ∈ {"mean", "cls"} = "mean"  # Embedding pooling strategy
  scoring: str ∈ {"softmax", "diff"} = "softmax"

Output:
  raw_scores: np.ndarray                   # Shape (N, M), values in [0, 1]

---

# ── PHASE 1: Embed all prototypes ──────────────────────────────────────

condition_centroids = []   # List of (c_pos, c_neg, has_pos, has_neg)

FOR EACH condition C in condition_set:

    positives = [p for p in C.prototypes if p.is_member == 1]
    negatives = [p for p in C.prototypes if p.is_member == 0]

    has_pos = len(positives) > 0
    has_neg = len(negatives) > 0

    IF has_pos:
        P_pos_embeddings = []
        FOR EACH proto in positives:
            e = BERT_embed(proto.prototype_text, model, pooling)
            e = e / ||e||_2
            P_pos_embeddings.append(proto.weight * e)
        # Weighted centroid
        c_pos = sum(P_pos_embeddings) / sum(p.weight for p in positives)
        c_pos = c_pos / ||c_pos||_2
    ELSE:
        c_pos = None

    IF has_neg:
        P_neg_embeddings = []
        FOR EACH proto in negatives:
            e = BERT_embed(proto.prototype_text, model, pooling)
            e = e / ||e||_2
            P_neg_embeddings.append(proto.weight * e)
        # Weighted centroid
        c_neg = sum(P_neg_embeddings) / sum(p.weight for p in negatives)
        c_neg = c_neg / ||c_neg||_2
    ELSE:
        c_neg = None

    condition_centroids.append((c_pos, c_neg, has_pos, has_neg))


# ── PHASE 2: Batch-embed all texts ─────────────────────────────────────

T = BERT_embed_batch(texts, model, pooling)    # Shape: (N, d)
T = T / ||T||_rowwise                           # Row-wise L2 normalize


# ── PHASE 3 + 4: Compute raw scores per condition ───────────────────────

raw_scores = np.zeros((N, M))

FOR j, (c_pos, c_neg, has_pos, has_neg) IN enumerate(condition_centroids):

    IF NOT has_pos AND NOT has_neg:
        # Edge case 6.1: no prototypes at all
        raw_scores[:, j] = 0.0
        CONTINUE

    IF NOT has_neg:
        # Edge case 6.2: positive-only
        sim_pos = T @ c_pos                    # Shape (N,)
        raw_scores[:, j] = (sim_pos + 1.0) / 2.0
        CONTINUE

    IF NOT has_pos:
        # Edge case 6.3: negative-only
        sim_neg = T @ c_neg
        raw_scores[:, j] = (1.0 - sim_neg) / 2.0
        CONTINUE

    # Full case: both positive and negative centroids
    sim_pos = T @ c_pos                        # Shape (N,)
    sim_neg = T @ c_neg                        # Shape (N,)

    IF scoring == "softmax":
        # Eq. 1: Softmax with temperature
        raw_scores[:, j] = np.exp(temperature * sim_pos) / (
            np.exp(temperature * sim_pos) + np.exp(temperature * sim_neg)
        )
    ELSE:
        # Eq. 3: Normalized difference (fallback)
        raw_scores[:, j] = np.clip(
            (sim_pos - sim_neg + 1.0) / 2.0, 0.0, 1.0
        )

    # Handle empty-text edge case (6.5): zero-vector produces cosine ≈ 0
    # for both. Softmax → 0.5, diff → 0.5. Are there any NaN vectors?
    nan_mask = np.isnan(raw_scores[:, j])
    raw_scores[nan_mask, j] = 0.5


RETURN raw_scores   # Feed into existing calibration pipeline
```

---

## 8. Integration with Existing Calibration Pipeline

The `raw_scores` output replaces what `ChineseKeywordDictionary.match_corpus()` produces
for keyword-based conditions. The pipeline is:

```
BERT Prototype Engine                     Existing Calibration Layer
─────────────────────                     ──────────────────────────
texts + prototypes                        (unchanged)
       │                                        │
       ▼                                        │
  BERT embed (ONNX / JS)                        │
       │                                        │
       ▼                                        │
  Cosine → Softmax → raw ∈ [0,1]                │
       │                                        │
       └────────────────────────────────────────┘
                       │
                       ▼
              _apply_calibration(raw, method, params)
                       │
              ┌────────┼────────┬──────────┐
              ▼        ▼        ▼          ▼
           Direct  Indirect  Ragin   Passthrough
                       │
                       ▼
              membership ∈ [0, 1]
```

The new `ScoringSource.BERT` value would slot into `_compute_raw_scores()` in parallel
with the existing `KEYWORD` and `HYBRID` branches.

The calibration strategies **do not need modification** — they accept raw scores in any
monotonic range. For RaginCalibration, the raw scores should be in [0, 1], which the
softmax formula guarantees.

---

## 9. Computational Complexity

| Phase | Operation | Complexity |
|-------|-----------|------------|
| Prototype embedding | K BERT forward passes | O(K · L² · d) where L = avg seq len |
| Text embedding | 1 batched BERT forward pass | O(N · L² · d) |
| Centroid computation | K vector operations | O(K · d) |
| Cosine similarity | 2 matrix-vector products per condition | O(N · d · M) |
| Softmax | 2M vector ops | O(N · M) |

**Total:** O((K + N) · L² · d + N · d · M)

**Comparison with current bigram approach:** Current is O(N · M · K · L). Both are
dominated by text length, but BERT's constant factor for the L² · d term is much
larger (neural network forward pass vs character sliding window).

**Key optimization:** Prototype embedding is done once and cached. For repeated
analyses with the same condition set but different texts, only Phase 2-4 re-execute.

---

## 10. Theoretical Basis: Why This Algorithm is QCA-Valid

### 10.1 Prototype Theory (Rosch 1973, Hampton 1995)

Prototype theory posits that human categorization works through comparison to a
"prototype" — an abstract central tendency of category members. The degree of
category membership is proportional to the similarity to this prototype.

This algorithm operationalizes the theory directly:
- **Prototype text** = The researcher's operational definition of the category
- **BERT embedding** = A dense vector capturing the semantics of the text
- **Centroid** = The mathematical "summary representation" (central tendency)
- **Cosine similarity** = Quantitative "family resemblance" to the prototype
- **Softmax score** = Graded category membership based on relative resemblance

### 10.2 Fuzzy-Set QCA (Ragin 2000, 2008)

Fuzzy-set QCA requires:
1. Sets are theoretically defined (not inductively discovered)
2. Membership is graded in [0, 1]
3. The crossover point (0.5) represents maximum ambiguity
4. Calibration requires substantive/theoretical knowledge

This algorithm preserves all four requirements:
1. **Theoretically defined**: Prototypes are defined by the researcher, not learned
2. **Graded membership**: Softmax produces continuous (0,1) values
3. **Crossover at 0.5**: When sim_pos = sim_neg, raw = 0.5 (maximum ambiguity)
4. **Theoretical calibration**: Softmax output is a monotonic raw score — the researcher still defines where 0.05, 0.50, and 0.95 membership fall via calibration thresholds

### 10.3 Key Theoretical Tension Resolved

The tension between "BERT as statistical model" and "QCA as theoretical method" is
resolved by the **two-stage design**:

- **Stage A (BERT)**: Answers "how semantically similar is this text to the prototype?"
  — a measurement, not a judgment.
- **Stage B (Calibration)**: Answers "what degree of similarity constitutes membership?"
  — the researcher's theoretical judgment.

BERT provides the measure; the scholar provides the calibration. This preserves the
QCA methodological requirement while replacing lexical matching with semantic matching.

---

## 11. Hyperparameters and Defaults

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `pooling` | `"mean"` | {mean, cls} | Embedding aggregation strategy |
| `scoring` | `"softmax"` | {softmax, diff} | Cosine-to-raw-score formula |
| `temperature` | `5.0` | (0, ∞) | Softmax sharpness; higher = more discrimination |
| `embedding_dim` | `768` | N/A | Model-dependent (bert-base = 768, MiniLM = 384) |
| `l2_normalize` | `true` | {true, false} | Whether to L2-normalize embeddings before cosine |

**Tuning temperature:** The temperature should be calibrated so that the range of
raw scores across the corpus is [0.10, 0.90] or wider. If scores are compressed
near 0.5, increase τ. If scores are clustered at 0 and 1, decrease τ.

**Per-condition temperature:** Conditions with more prototypes (stronger theoretical
grounding) generally benefit from higher τ. Conditions with few prototypes (weaker
grounding) should use lower τ to avoid overfitting.

---

## 12. Appendix: Numerical Stability Notes

### 12.1 Softmax Overflow Prevention

For extreme cosine values with high temperature, `exp(τ · sim)` can overflow float64:

```
# Numerically stable softmax:
a = τ · sim_pos
b = τ · sim_neg
m = max(a, b)
raw = exp(a - m) / (exp(a - m) + exp(b - m))                           (Eq. 6)
```

This is mathematically equivalent to Eq. 1 but avoids overflow.

### 12.2 Zero-Vector Handling

When text is empty, `h = mean(zero_matrix) = zero_vector`. After L2 normalization,
`0/0 = NaN`. Guard with:

```
IF ||h||_2 < ε:
    e_T = zero_vector    # cosine(zero, anything) = 0 via convention
ELSE:
    e_T = h / ||h||_2
```

### 12.3 Cosine Clipping

Floating-point rounding can produce `cosine > 1.0` or `< -1.0`:

```
cosine = np.clip(cosine, -1.0, 1.0)
```
