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

import numpy as np

# ─── Calibrate: texts + condition set → fuzzy-set membership ───────────────


def handle_calibrate(texts_path, condition_set_path, output_path):
    """Calibrate text corpus entries against a condition set.

    Args:
        texts_path: VFS path to JSON array of text corpus entries
                    (list of {text_id, text, metadata}).
        condition_set_path: VFS path to JSON dict of condition set config.
        output_path: VFS path to write the fuzzy-set membership JSON result.
    """
    from experiment_engine.models import FuzzySetData, TrainingSample
    from experiment_engine.text_calibration.calibrator import TextCalibrationStage
    from experiment_engine.text_calibration.condition import _condition_set_from_dict

    with open(texts_path, encoding="utf-8") as f:
        _texts = json.load(f)
    with open(condition_set_path, encoding="utf-8") as f:
        _cs_dict = json.load(f)
    _condition_set = _condition_set_from_dict(_cs_dict)

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

    # Accumulate calibration results for all samples
    _fuzzy_data = None
    for _s in _samples:
        _result = _calibrator.calibrate_one(_s)
        if _fuzzy_data is None:
            _fuzzy_data = _result
        else:
            _fuzzy_data = FuzzySetData(
                membership=np.vstack([_fuzzy_data.membership, _result.membership]),
                case_ids=_fuzzy_data.case_ids + _result.case_ids,
                condition_names=_fuzzy_data.condition_names,
                outcome_name=_fuzzy_data.outcome_name,
                texts=_fuzzy_data.texts + _result.texts,
                metadata={},
            )

    if _fuzzy_data is not None:
        _json_out = {
            "membership": _fuzzy_data.membership.tolist(),
            "case_ids": _fuzzy_data.case_ids,
            "condition_names": _fuzzy_data.condition_names,
            "outcome_name": _fuzzy_data.outcome_name,
            "texts": _fuzzy_data.texts,
            "metadata": _fuzzy_data.metadata,
        }
    else:
        _json_out = {
            "membership": [],
            "case_ids": [],
            "condition_names": [],
            "outcome_name": "",
            "texts": [],
            "metadata": {},
        }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(_json_out, f, ensure_ascii=False)


# ─── Calibrate Prototype: text cases + prototype condition set → fuzzy-set ──


def handle_calibrate_prototype(text_cases_path, condition_set_path, output_path):
    """Calibrate using prototype-based similarity (instead of keyword matching).

    Args:
        text_cases_path: VFS path to JSON array of text cases
                         (list of {text_id, text, outcome}).
        condition_set_path: VFS path to JSON dict of condition set config.
        output_path: VFS path to write the fuzzy-set membership JSON result.
    """
    from experiment_engine.models import InputData
    from experiment_engine.text_calibration.calibrator import TextCalibrationStage
    from experiment_engine.text_calibration.condition import _condition_set_from_dict

    with open(text_cases_path, encoding="utf-8") as f:
        _cases = json.load(f)
    with open(condition_set_path, encoding="utf-8") as f:
        _cs_dict = json.load(f)
    _condition_set = _condition_set_from_dict(_cs_dict)

    _texts = [c["text"] for c in _cases]
    _outcomes = np.array([c.get("outcome", 0) for c in _cases], dtype=np.float64)
    _case_ids = [c["text_id"] for c in _cases]

    _calibrator = TextCalibrationStage(condition_set=_condition_set)
    _calibrator.setup()

    _data = InputData(data=np.array(_texts, dtype=object), index=_case_ids)
    _result = _calibrator.process_with_outcome(_data, _outcomes)
    _fuzzy = _result.processed

    _json_out = {
        "membership": _fuzzy.membership.tolist(),
        "case_ids": _fuzzy.case_ids,
        "condition_names": _fuzzy.condition_names,
        "outcome_name": _fuzzy.outcome_name,
        "texts": _texts,
        "metadata": _fuzzy.metadata,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(_json_out, f, ensure_ascii=False)


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
        if not c.keywords:
            warnings.append(f"Condition '{c.name}' has no keywords")
        if c.calibration_params is None:
            warnings.append(f"Condition '{c.name}' has no calibration parameters")

    valid = len(warnings) == 0

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"valid": valid, "warnings": warnings}, f, ensure_ascii=False)
