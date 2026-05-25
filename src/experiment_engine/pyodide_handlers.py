"""
Pyodide worker handler functions.

Each function follows the same contract:
1. Read input JSON file(s) from Pyodide VFS (written by the worker via FS.writeFile)
2. Perform QCA computation using the experiment_engine package
3. Write output JSON to Pyodide VFS (read by the worker via FS.readFile)

This file is part of the experiment_engine package and is covered by
pytest / ruff / mypy — unlike the raw Python strings previously embedded
in pyodide.worker.ts.
"""

import json
from contextlib import suppress

import numpy as np

# ─── Helper: serialize MembershipData to JSON ──────────────────────────────


def _serialize_fuzzy(fuzzy):
    """Serialize a MembershipData / FuzzySetData object to a JSON-compatible dict.

    Returns an empty-skeleton dict when ``fuzzy`` is None.
    """
    if fuzzy is None:
        return {
            "membership": [],
            "case_ids": [],
            "condition_names": [],
            "outcome_name": "",
            "texts": [],
            "metadata": {},
        }
    return {
        "membership": fuzzy.membership.tolist(),
        "case_ids": fuzzy.case_ids,
        "condition_names": fuzzy.condition_names,
        "outcome_name": fuzzy.outcome_name,
        "texts": fuzzy.texts,
        "metadata": fuzzy.metadata,
    }


# ─── Calibrate: texts + condition set → fuzzy-set membership ───────────────


def handle_calibrate(
    texts_path, condition_set_path, output_path, prototype_texts_path=None
):
    """Unified calibration handler — always uses keyword matching.

    Calibrates the raw text corpus through the keyword pipeline. If
    ``prototype_texts_path`` is provided, also calibrates those texts
    through the **same** keyword pipeline and returns both result sets.

    Args:
        texts_path: VFS path to JSON array of text corpus entries
                    (list of {text_id, text, metadata}).
        condition_set_path: VFS path to JSON dict of condition set config.
        output_path: VFS path to write output JSON.
        prototype_texts_path: Optional VFS path to JSON array of prototype
                    text cases (list of {text_id, text, outcome}).
                    When provided the output contains both ``fuzzyData``
                    and ``fuzzyDataPrototype``; otherwise only the raw
                    MembershipData is returned (backward compatibility).

    Returns:
        Nothing — writes JSON to *output_path*.
    """
    from experiment_engine.models import FuzzySetData, InputData, TrainingSample
    from experiment_engine.text_calibration.calibrator import TextCalibrationStage
    from experiment_engine.text_calibration.condition import _condition_set_from_dict

    with open(condition_set_path, encoding="utf-8") as f:
        _cs_dict = json.load(f)
    _condition_set = _condition_set_from_dict(_cs_dict)

    # ── Raw texts (keyword pipeline) ───────────────────────────────────
    with open(texts_path, encoding="utf-8") as f:
        _texts = json.load(f)

    _samples = [
        TrainingSample(
            text_id=_t["text_id"],
            text=_t["text"],
            metadata=_t.get("metadata", {}),
        )
        for _t in _texts
    ]

    _calibrator = TextCalibrationStage(condition_set=_condition_set)
    _calibrator.setup()

    _raw_fuzzy = None
    for _s in _samples:
        _result = _calibrator.calibrate_one(_s)
        if _raw_fuzzy is None:
            _raw_fuzzy = _result
        else:
            _raw_fuzzy = FuzzySetData(
                membership=np.vstack([_raw_fuzzy.membership, _result.membership]),
                case_ids=_raw_fuzzy.case_ids + _result.case_ids,
                condition_names=_raw_fuzzy.condition_names,
                outcome_name=_raw_fuzzy.outcome_name,
                texts=_raw_fuzzy.texts + _result.texts,
                metadata={},
            )

    # ── Prototype texts (optional, same keyword pipeline) ──────────────
    _proto_fuzzy = None
    if prototype_texts_path is not None:
        with open(prototype_texts_path, encoding="utf-8") as f:
            _cases = json.load(f)

        _p_texts = [c["text"] for c in _cases]
        _p_outcomes = np.array([c.get("outcome", 0) for c in _cases], dtype=np.float64)
        _p_case_ids = [c["text_id"] for c in _cases]

        _proto_calibrator = TextCalibrationStage(condition_set=_condition_set)
        _proto_calibrator.setup()

        _p_data = InputData(data=np.array(_p_texts, dtype=object), index=_p_case_ids)
        _p_result = _proto_calibrator.process_with_outcome(_p_data, _p_outcomes)
        _proto_fuzzy = _p_result.processed

    # ── Write output ──────────────────────────────────────────────────
    if prototype_texts_path is not None:
        # Unified output: both raw and prototype MembershipData
        _output = {
            "fuzzyData": _serialize_fuzzy(_raw_fuzzy),
            "fuzzyDataPrototype": _serialize_fuzzy(_proto_fuzzy),
        }
    else:
        # Backward-compatible: raw MembershipData directly at top level
        _output = _serialize_fuzzy(_raw_fuzzy)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(_output, f, ensure_ascii=False)


# ─── Calibrate Prototype (backward-compatible wrapper) ─────────────────────


def handle_calibrate_prototype(text_cases_path, condition_set_path, output_path):
    """Calibrate prototype texts — backward-compatible wrapper.

    **Deprecated.**  Prefer ``handle_calibrate(prototype_texts_path=...)``
    which runs prototype texts through the same keyword calibration
    pipeline and can return both raw and prototype results in a single
    call.

    This wrapper delegates to the unified handler and extracts the
    prototype-only result, preserving the original output format.
    """
    import os

    # Write a minimal (empty) raw-texts file so the unified handler has
    # something for its required ``texts_path`` argument.
    _empty_path = "/tmp/_handle_calibrate_prototype_empty_raw.json"
    _temp_output = "/tmp/_handle_calibrate_prototype_unified_out.json"

    with open(_empty_path, "w", encoding="utf-8") as f:
        json.dump([], f)

    try:
        handle_calibrate(
            _empty_path,
            condition_set_path,
            _temp_output,
            prototype_texts_path=text_cases_path,
        )
        with open(_temp_output, encoding="utf-8") as f:
            _result = json.load(f)
        _output = _result.get(
            "fuzzyDataPrototype",
            {
                "membership": [],
                "case_ids": [],
                "condition_names": [],
                "outcome_name": "",
                "texts": [],
                "metadata": {},
            },
        )
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(_output, f, ensure_ascii=False)
    finally:
        for _p in (_empty_path, _temp_output):
            with suppress(OSError):
                os.remove(_p)


# ─── Analyze: fuzzy data → truth table + solutions + necessity/sufficiency ──


def handle_analyze(fuzzy_data_path, params_path, output_path):
    """Run full QCA analysis on fuzzy-set data.

    Args:
        fuzzy_data_path: VFS path to JSON dict of fuzzy-set data
                         ({membership, case_ids, condition_names, outcome_name, ...}).
        params_path: VFS path to JSON dict of analysis params
                     ({consistency_threshold, frequency_threshold}).
        output_path: VFS path to write the QCA analysis result JSON.
    """
    from experiment_engine.models import FuzzySetData
    from experiment_engine.qca_engine.analyzer import QCAnalyzerStage

    with open(fuzzy_data_path, encoding="utf-8") as f:
        _fd_dict = json.load(f)
    with open(params_path, encoding="utf-8") as f:
        _params = json.load(f)

    _fuzzy = FuzzySetData(
        membership=np.array(_fd_dict["membership"]),
        case_ids=_fd_dict.get("case_ids"),
        condition_names=_fd_dict.get("condition_names", []),
        outcome_name=_fd_dict.get("outcome_name", ""),
        texts=_fd_dict.get("texts"),
        metadata=_fd_dict.get("metadata", {}),
    )

    _analyzer = QCAnalyzerStage(
        consistency_threshold=_params.get("consistency_threshold", 0.75),
        frequency_threshold=_params.get("frequency_threshold", 1.0),
    )
    _analyzer.setup()
    _result = _analyzer.analyze(_fuzzy)

    _out = _result.model_dump(mode="json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(_out, f, ensure_ascii=False, default=str)


# ─── Robustness ─────────────────────────────────────────────────────────────


def handle_robustness(fuzzy_data_path, analysis_result_path, output_path):
    """Run robustness/sensitivity tests on a QCA analysis result.

    Args:
        fuzzy_data_path: VFS path to JSON dict of fuzzy-set data.
        analysis_result_path: VFS path to JSON dict of QCAAnalysisResult.
        output_path: VFS path to write the robustness report JSON.
    """
    from experiment_engine.models import FuzzySetData, QCAAnalysisResult
    from experiment_engine.qca_engine.advanced.robustness import RobustnessTester

    with open(fuzzy_data_path, encoding="utf-8") as f:
        _fd_dict = json.load(f)
    with open(analysis_result_path, encoding="utf-8") as f:
        _ar_dict = json.load(f)

    _fuzzy = FuzzySetData(
        membership=np.array(_fd_dict["membership"]),
        case_ids=_fd_dict.get("case_ids"),
        condition_names=_fd_dict.get("condition_names", []),
        outcome_name=_fd_dict.get("outcome_name", ""),
    )

    _baseline = QCAAnalysisResult(**_ar_dict)

    _tester = RobustnessTester()
    _report = _tester.run_all(_fuzzy, _baseline)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(_report.model_dump(mode="json"), f, ensure_ascii=False, default=str)


# ─── Counterfactuals ────────────────────────────────────────────────────────


def handle_counterfactuals(fuzzy_data_path, analysis_result_path, output_path):
    """Run counterfactual analysis on a QCA analysis result.

    Args:
        fuzzy_data_path: VFS path to JSON dict of fuzzy-set data.
        analysis_result_path: VFS path to JSON dict of QCAAnalysisResult.
        output_path: VFS path to write the counterfactual report JSON.
    """
    from experiment_engine.models import FuzzySetData, QCAAnalysisResult
    from experiment_engine.qca_engine.advanced.counterfactual import (
        CounterfactualAnalyzer,
    )

    with open(fuzzy_data_path, encoding="utf-8") as f:
        _fd_dict = json.load(f)
    with open(analysis_result_path, encoding="utf-8") as f:
        _ar_dict = json.load(f)

    _fuzzy = FuzzySetData(
        membership=np.array(_fd_dict["membership"]),
        case_ids=_fd_dict.get("case_ids"),
        condition_names=_fd_dict.get("condition_names", []),
        outcome_name=_fd_dict.get("outcome_name", ""),
    )

    _baseline = QCAAnalysisResult(**_ar_dict)

    _cf_analyzer = CounterfactualAnalyzer()
    _report = _cf_analyzer.analyze(_fuzzy, _baseline)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(_report.model_dump(mode="json"), f, ensure_ascii=False, default=str)


# ─── Load Corpus: raw content → TextCorpusEntry[] via TextCorpusReader ───────


def handle_load_corpus(corpus_config_path, output_path):
    """Parse raw text corpus content using TextCorpusReader.

    Replaces the former frontend parseTextContent() with Python-side
    parsing so that CSV/JSON/TXT logic lives in a single location.

    Args:
        corpus_config_path: VFS path to JSON with keys
            ``fileName`` (str), ``content`` (str), ``format``
            (one of ``csv``, ``json``, ``txt``).
        output_path: VFS path to write the JSON array of
            ``{text_id, text, metadata}`` entries.
    """
    from experiment_engine.io.readers import TextCorpusReader

    with open(corpus_config_path, encoding="utf-8") as f:
        config = json.load(f)

    vfs_file = f"/tmp/{config['fileName']}"
    _fmt = config.get("format", "csv")
    if _fmt == "xlsx":
        # Binary content is base64-encoded by the worker
        import base64 as _b64

        with open(vfs_file, "wb") as f:
            f.write(_b64.b64decode(config["content"]))
    else:
        with open(vfs_file, "w", encoding="utf-8") as f:
            f.write(config["content"])

    reader = TextCorpusReader()
    result = reader.read(vfs_file)

    entries = []
    for i in range(len(result.data)):
        text_id = (
            result.index[i]
            if result.index and i < len(result.index)
            else f"case_{i + 1}"
        )
        entries.append(
            {
                "text_id": str(text_id),
                "text": str(result.data[i]),
                "metadata": {},
            }
        )

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False)


# ─── Export ─────────────────────────────────────────────────────────────────


def handle_export(result_path, config_path, output_path):
    """Export a QCA analysis result in the requested format.

    Args:
        result_path: VFS path to JSON dict of QCAAnalysisResult.
        config_path: VFS path to JSON dict with format key
                     (e.g. {"format": "csv"}).
        output_path: VFS path to write an output descriptor JSON with
                     keys ``data`` (exported content string) and ``mime``
                     (MIME type string).
    """
    import csv as _csv
    import io

    from experiment_engine.models import QCAAnalysisResult
    from experiment_engine.report.qca_reporter import QCALaTeXReporter

    with open(result_path, encoding="utf-8") as f:
        _ar_dict = json.load(f)
    with open(config_path, encoding="utf-8") as f:
        _config = json.load(f)

    _result = QCAAnalysisResult(**_ar_dict)
    fmt = _config.get("format", "json")

    if fmt == "json":
        out = json.dumps(
            _result.model_dump(mode="json"),
            indent=2,
            ensure_ascii=False,
            default=str,
        )
        mime = "application/json"
    elif fmt == "csv":
        buf = io.StringIO()
        if _result.fuzzy_data:
            w = _csv.writer(buf)
            header = [
                *_result.fuzzy_data.condition_names,
                _result.fuzzy_data.outcome_name,
            ]
            w.writerow(header)
            for row in _result.fuzzy_data.membership:
                w.writerow(row.tolist())
        out = buf.getvalue()
        mime = "text/csv"
    elif fmt == "latex":
        _reporter = QCALaTeXReporter()
        out = _reporter.generate(_result)
        mime = "application/x-latex"
    else:
        raise ValueError(f"Unknown export format: {fmt}")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"data": out, "mime": mime}, f, ensure_ascii=False)


# ─── Validate Condition Set ─────────────────────────────────────────────────


def handle_validate(condition_set_path, output_path):
    """Validate a condition set definition.

    Args:
        condition_set_path: VFS path to JSON dict of condition set config.
        output_path: VFS path to write the validation result JSON
                     ({"valid": bool, "warnings": [str]}).
    """
    from experiment_engine.text_calibration.condition import _condition_set_from_dict

    with open(condition_set_path, encoding="utf-8") as f:
        _cs_dict = json.load(f)
    _cs = _condition_set_from_dict(_cs_dict)

    warnings = []
    if not _cs.conditions:
        warnings.append("No causal conditions defined")
    if _cs.outcome is None:
        warnings.append("No outcome condition defined")
    for c in _cs.conditions:
        if not c.prototypes:
            warnings.append(f"Condition '{c.name}' has no prototypes")
        if c.calibration_params is None:
            warnings.append(f"Condition '{c.name}' has no calibration parameters")

    valid = len(warnings) == 0

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"valid": valid, "warnings": warnings}, f, ensure_ascii=False)


# ─── Embed Calibrate: embedding-based prototype cosine similarity ─────────────


def handle_embed_calibrate(texts_path, condition_set_path, output_path):
    """Calibrate texts using pre-computed BERT embeddings via CosineSimilarityEngine.

    Replaces keyword matching with prototype-based cosine similarity scoring
    from pre-computed embeddings (computed in the browser by Transformers.js).

    Args:
        texts_path: VFS path to JSON array of text entries, each with
                    ``{text_id, text, embedding: [768 floats]}``.
        condition_set_path: VFS path to JSON dict of condition set config.
        output_path: VFS path to write the MembershipData JSON.

    Returns:
        Nothing — writes MembershipData JSON to *output_path*.
    """
    from experiment_engine.models import MembershipData
    from experiment_engine.text_calibration.condition import _condition_set_from_dict
    from experiment_engine.text_calibration.cosine_similarity import (
        CosineSimilarityEngine,
    )
    from experiment_engine.text_calibration.strategies import (
        CalibrationStrategyRegistry,
    )

    # ── Load condition set ───────────────────────────────────────────
    with open(condition_set_path, encoding="utf-8") as f:
        _cs_dict = json.load(f)
    _condition_set = _condition_set_from_dict(_cs_dict)

    # ── Load texts with embeddings ───────────────────────────────────
    with open(texts_path, encoding="utf-8") as f:
        _texts = json.load(f)

    _n_texts = len(_texts)

    # ── Collect all conditions (causal + outcome) ────────────────────
    _all_conditions = list(_condition_set.conditions)
    if _condition_set.outcome:
        _all_conditions.append(_condition_set.outcome)

    # ── Build raw-dict lookup for prototype_embeddings ───────────────
    # _condition_from_dict does not yet deserialise prototype_embeddings,
    # so we extract them from the raw JSON dict.
    _raw_conds: dict[str, dict] = {}
    for _c in _cs_dict.get("conditions", []):
        _raw_conds[_c["name"]] = _c
    if _cs_dict.get("outcome"):
        _raw_conds[_cs_dict["outcome"]["name"]] = _cs_dict["outcome"]

    # ── Build condition_prototypes + prototype_embeddings dicts ──────
    _condition_prototypes: dict[str, list[dict]] = {}
    _prototype_embeddings: dict[str, np.ndarray] = {}

    for _cond in _all_conditions:
        _raw = _raw_conds.get(_cond.name, {})
        _pe = _raw.get("prototype_embeddings")
        if _pe and len(_pe) > 0 and len(_cond.prototypes) > 0:
            _condition_prototypes[_cond.name] = [
                {
                    "prototype_text": _p.prototype_text,
                    "is_member": _p.is_member,
                    "weight": _p.weight,
                }
                for _p in _cond.prototypes
            ]
            _prototype_embeddings[_cond.name] = np.array(_pe, dtype=np.float64)

    # ── Determine embedding dimension ────────────────────────────────
    _emb_dim = 768
    for _e in _prototype_embeddings.values():
        _emb_dim = _e.shape[1]
        break

    # ── Build text embeddings array ──────────────────────────────────
    if _n_texts > 0:
        _text_embeddings = np.array([t["embedding"] for t in _texts], dtype=np.float64)
    else:
        _text_embeddings = np.zeros((0, _emb_dim), dtype=np.float64)

    # ── Compute raw scores via CosineSimilarityEngine ────────────────
    _engine = CosineSimilarityEngine(
        temperature=5.0, aggregation="centroid", scoring="softmax"
    )
    if _condition_prototypes:
        _raw_scores = _engine.compute_scores(
            _text_embeddings, _condition_prototypes, _prototype_embeddings
        )
    else:
        _raw_scores = np.zeros((_n_texts, 0), dtype=np.float64)

    # ── Apply calibration per condition ──────────────────────────────
    _cond_names_with_embeddings = list(_condition_prototypes.keys())
    _m_conds = len(_all_conditions)
    _membership = np.zeros((_n_texts, _m_conds), dtype=np.float64)
    _registry = CalibrationStrategyRegistry()

    for _j, _cond in enumerate(_all_conditions):
        if _cond.name in _condition_prototypes:
            _col_idx = _cond_names_with_embeddings.index(_cond.name)
            _raw_col = _raw_scores[:, _col_idx]
        else:
            _raw_col = np.zeros(_n_texts, dtype=np.float64)

        if _cond.calibration_params is not None:
            _strategy = _registry.get(_cond.calibration_type)
            _membership[:, _j] = _strategy.calibrate(_raw_col, _cond.calibration_params)
        else:
            _membership[:, _j] = _raw_col

    # ── Build MembershipData ─────────────────────────────────────────
    _fuzzy = MembershipData(
        membership=_membership,
        case_ids=[t["text_id"] for t in _texts],
        condition_names=_condition_set.condition_names,
        outcome_name=(_condition_set.outcome.name if _condition_set.outcome else ""),
        texts=[t.get("text", "") for t in _texts],
        metadata={},
    )

    # ── Write output ─────────────────────────────────────────────────
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(_serialize_fuzzy(_fuzzy), f, ensure_ascii=False)
