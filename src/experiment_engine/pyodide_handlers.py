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
    """Serialize a MembershipData / MembershipData object to a JSON-compatible dict.

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
    texts_path,
    condition_set_path,
    output_path,
    prototype_texts_path=None,
    prototype_output_path=None,
):
    """Calibrate raw texts through the keyword pipeline.

    This function ALWAYS returns flat MembershipData (raw text calibration).
    Prototype calibration can be written to a separate file via the
    ``prototype_output_path`` parameter, or obtained by calling
    ``handle_calibrate_prototype()`` separately.

    Args:
        texts_path: VFS path to JSON array of text corpus entries
                    (list of {text_id, text, metadata}).
        condition_set_path: VFS path to JSON dict of condition set config.
        output_path: VFS path to write output JSON (flat MembershipData).
        prototype_texts_path: Optional VFS path to JSON array of prototype
                    text cases (list of {text_id, text, outcome}).
                    When provided, prototype texts are also calibrated through
                    the same keyword pipeline.
        prototype_output_path: Optional VFS path to write prototype calibration
                    results as a separate flat MembershipData JSON file.
                    Only used when ``prototype_texts_path`` is also provided.

    Returns:
        Nothing — writes flat MembershipData JSON to *output_path*.
    """
    from experiment_engine.models import InputData, TrainingSample
    from experiment_engine.text_calibration.calibrator import TextCalibrationStage
    from experiment_engine.text_calibration.condition import _condition_set_from_dict

    with open(condition_set_path, encoding="utf-8") as f:
        _cs_dict = json.load(f)
    if not isinstance(_cs_dict, dict):
        raise TypeError(
            f"condition_set JSON must be a dict, got {type(_cs_dict).__name__}. "
            "Frontend likely passed raw YAML string instead of parsed ConditionSet object."
        )
    _condition_set = _condition_set_from_dict(_cs_dict)

    # ── Validate condition set has conditions ───────────────────────────
    _n_conds = len(_condition_set.conditions)
    _has_outcome = _condition_set.outcome is not None
    if _n_conds == 0 and not _has_outcome:
        _keys = list(_cs_dict.keys())
        raise ValueError(
            f"Condition set has 0 conditions and no outcome. "
            f"JSON keys: {_keys}. "
            f"conditions field type: {type(_cs_dict.get('conditions')).__name__}. "
            f"outcome field type: {type(_cs_dict.get('outcome')).__name__}. "
            f"Check that the frontend is sending a valid ConditionSet object "
            f"(yamlContent parsed via yamlToConditionSet, not passed as raw string)."
        )

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

    # Calibrate all columns (conditions + outcome) through the normal
    # text-scoring pipeline so that every column produces fuzzy-set values.
    # The CSV expected_outcome values (0/1 ground truth) are still available
    # in entry metadata for downstream display/reference, but the outcome
    # membership itself is computed from text similarity just like conditions.
    _texts_list = [_s.text for _s in _samples]
    _case_ids = [_s.text_id for _s in _samples]
    _raw_input = InputData(data=np.array(_texts_list, dtype=object), index=_case_ids)

    _raw_result = _calibrator.process(_raw_input)
    _raw_fuzzy = _raw_result.processed

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
    # ALWAYS write flat MembershipData (raw text calibration).
    # Prototype calibration, when requested, is written to a separate file.
    _output = _serialize_fuzzy(_raw_fuzzy)

    if prototype_texts_path is not None and prototype_output_path is not None:
        with open(prototype_output_path, "w", encoding="utf-8") as f:
            json.dump(_serialize_fuzzy(_proto_fuzzy), f, ensure_ascii=False)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(_output, f, ensure_ascii=False)


# ─── Calibrate Prototype (backward-compatible wrapper) ─────────────────────


def handle_calibrate_prototype(text_cases_path, condition_set_path, output_path):
    """Calibrate prototype texts — backward-compatible wrapper.

    **Deprecated.**  Prefer calling ``handle_calibrate()`` with
    ``prototype_texts_path`` and ``prototype_output_path`` to write
    prototype calibration to a separate file.

    This wrapper delegates to the unified handler with a dummy raw-texts
    file and reads back the prototype result from the separate output path.
    """
    import os

    # Write a minimal (empty) raw-texts file so the unified handler has
    # something for its required ``texts_path`` argument.
    _empty_path = "/tmp/_handle_calibrate_prototype_empty_raw.json"
    _temp_output = "/tmp/_handle_calibrate_prototype_unified_out.json"
    _proto_temp = "/tmp/_handle_calibrate_prototype_unified_proto.json"

    with open(_empty_path, "w", encoding="utf-8") as f:
        json.dump([], f)

    try:
        handle_calibrate(
            _empty_path,
            condition_set_path,
            _temp_output,
            prototype_texts_path=text_cases_path,
            prototype_output_path=_proto_temp,
        )
        with open(_proto_temp, encoding="utf-8") as f:
            _output = json.load(f)
        _ocn = _output.get("condition_names", [])
        _om = _output.get("membership", [])
        if not _ocn or not _om or not isinstance(_om, list) or len(_om) == 0:
            raise ValueError(
                f"Prototype calibration produced empty output: "
                f"condition_names={_ocn}, membership_rows={len(_om) if isinstance(_om, list) else type(_om).__name__}. "
                "Check that the condition set has conditions and the prototype texts are valid."
            )
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(_output, f, ensure_ascii=False)
    finally:
        for _p in (_empty_path, _temp_output, _proto_temp):
            with suppress(OSError):
                os.remove(_p)


# ─── Analyze: fuzzy data → truth table + solutions + necessity/sufficiency ──


def handle_analyze(fuzzy_data_path, params_path, output_path, condition_set_path=None):
    """Run full QCA analysis on fuzzy-set data.

    Args:
        fuzzy_data_path: VFS path to JSON dict of fuzzy-set data
                         ({membership, case_ids, condition_names, outcome_name, ...}).
        params_path: VFS path to JSON dict of analysis params
                     ({consistency_threshold, frequency_threshold}).
        output_path: VFS path to write the QCA analysis result JSON.
        condition_set_path: Optional VFS path to JSON dict of condition set config.
            When provided, the condition set is passed to QCAnalyzerStage for
            richer solution labels and condition metadata.
    """
    from experiment_engine.models import MembershipData
    from experiment_engine.qca_engine.analyzer import QCAnalyzerStage

    with open(fuzzy_data_path, encoding="utf-8") as f:
        _fd_dict = json.load(f)
    with open(params_path, encoding="utf-8") as f:
        _params = json.load(f)

    _fuzzy = MembershipData(
        membership=np.array(_fd_dict["membership"]),
        case_ids=_fd_dict.get("case_ids"),
        condition_names=_fd_dict.get("condition_names", []),
        outcome_name=_fd_dict.get("outcome_name", ""),
        texts=_fd_dict.get("texts"),
        metadata=_fd_dict.get("metadata", {}),
    )

    # Load condition set if provided — adds condition metadata to analyzer output
    _cs = None
    if condition_set_path:
        from experiment_engine.text_calibration.condition import (
            _condition_set_from_dict,
        )

        with open(condition_set_path, encoding="utf-8") as f:
            _cs_dict = json.load(f)
        _cs = _condition_set_from_dict(_cs_dict)

    _analyzer = QCAnalyzerStage(
        condition_set=_cs,
        consistency_threshold=_params.get("consistency_threshold", 0.75),
        frequency_threshold=_params.get("frequency_threshold", 1.0),
    )
    _analyzer.setup()
    _result = _analyzer.analyze(_fuzzy)

    # DIAG: log solution structure to browser console
    _sol = _result.solutions
    print(
        f"[diag] solutions.complex exists: {_sol.complex is not None}",
        file=__import__("sys").stderr,
        flush=True,
    )
    if _sol.complex is not None:
        print(
            f"[diag] complex.solution_consistency={_sol.complex.solution_consistency}",
            file=__import__("sys").stderr,
            flush=True,
        )
        print(
            f"[diag] complex.solution_coverage={_sol.complex.solution_coverage}",
            file=__import__("sys").stderr,
            flush=True,
        )
        print(
            f"[diag] complex.terms={_sol.complex.terms}",
            file=__import__("sys").stderr,
            flush=True,
        )
    else:
        print(
            f"[diag] complex is None — intermediate={_sol.intermediate is not None}, parsimonious={_sol.parsimonious is not None}",
            file=__import__("sys").stderr,
            flush=True,
        )
    print(
        f"[diag] sufficiency.solutions type: {type(_result.sufficiency.solutions).__name__}",
        file=__import__("sys").stderr,
        flush=True,
    )

    # Convert ndarray fields to plain Python lists so model_dump(mode="json")
    # doesn't choke on numpy types (which pydantic can't serialize in JSON mode).
    if _result.fuzzy_data is not None and isinstance(
        _result.fuzzy_data.membership, np.ndarray
    ):
        _result.fuzzy_data.membership = _result.fuzzy_data.membership.tolist()
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

    Raises:
        ValueError: If the fuzzy data is empty or the analysis result is
            missing required fields.
    """
    from experiment_engine.models import MembershipData, QCAAnalysisResult
    from experiment_engine.qca_engine.advanced.robustness import RobustnessTester

    with open(fuzzy_data_path, encoding="utf-8") as f:
        _fd_dict = json.load(f)
    with open(analysis_result_path, encoding="utf-8") as f:
        _ar_dict = json.load(f)

    _membership = np.array(_fd_dict.get("membership", []))
    if _membership.ndim != 2 or _membership.shape[0] == 0:
        raise ValueError(
            "Fuzzy data has 0 cases — cannot run robustness tests. "
            "Ensure calibration produced valid membership data before running robustness."
        )

    _fuzzy = MembershipData(
        membership=_membership,
        case_ids=_fd_dict.get("case_ids"),
        condition_names=_fd_dict.get("condition_names", []),
        outcome_name=_fd_dict.get("outcome_name", ""),
    )

    # Convert serialized lists back to ndarray for Pydantic model construction
    if _ar_dict.get("fuzzy_data") and isinstance(
        _ar_dict["fuzzy_data"].get("membership"), list
    ):
        _ar_dict["fuzzy_data"]["membership"] = np.array(
            _ar_dict["fuzzy_data"]["membership"], dtype=np.float64
        )

    _baseline = QCAAnalysisResult(**_ar_dict)

    # The RobustnessTester handles empty solutions gracefully
    # (_get_baseline_terms returns []) — no guard needed for solutions.
    _tester = RobustnessTester()
    try:
        _report = _tester.run_all(_fuzzy, _baseline)
    except Exception as _exc:
        raise RuntimeError(
            f"Robustness tests failed: {_exc}. "
            "Check that the analysis result contains valid solutions with "
            "non-empty truth table rows."
        ) from _exc

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(_report.model_dump(mode="json"), f, ensure_ascii=False, default=str)


# ─── Counterfactuals ────────────────────────────────────────────────────────


def handle_counterfactuals(fuzzy_data_path, analysis_result_path, output_path):
    """Run counterfactual analysis on a QCA analysis result.

    Args:
        fuzzy_data_path: VFS path to JSON dict of fuzzy-set data.
        analysis_result_path: VFS path to JSON dict of QCAAnalysisResult.
        output_path: VFS path to write the counterfactual report JSON.

    Raises:
        ValueError: If the analysis result contains no truth table.
    """
    from experiment_engine.models import MembershipData, QCAAnalysisResult
    from experiment_engine.qca_engine.advanced.counterfactual import (
        CounterfactualAnalyzer,
    )

    with open(fuzzy_data_path, encoding="utf-8") as f:
        _fd_dict = json.load(f)
    with open(analysis_result_path, encoding="utf-8") as f:
        _ar_dict = json.load(f)

    _fuzzy = MembershipData(
        membership=np.array(_fd_dict["membership"]),
        case_ids=_fd_dict.get("case_ids"),
        condition_names=_fd_dict.get("condition_names", []),
        outcome_name=_fd_dict.get("outcome_name", ""),
    )

    # Convert serialized lists back to ndarray for Pydantic model construction
    if _ar_dict.get("fuzzy_data") and isinstance(
        _ar_dict["fuzzy_data"].get("membership"), list
    ):
        _ar_dict["fuzzy_data"]["membership"] = np.array(
            _ar_dict["fuzzy_data"]["membership"], dtype=np.float64
        )

    _baseline = QCAAnalysisResult(**_ar_dict)

    if _baseline.truth_table is None:
        raise ValueError(
            "No truth table in analysis result — cannot run counterfactual analysis. "
            "Ensure the analysis stage produced a valid truth table."
        )

    _cf_analyzer = CounterfactualAnalyzer()
    _report = _cf_analyzer.analyze(_baseline.truth_table, None)

    # Produce all three solution types (matching api.py run_counterfactuals())
    complex_terms = _cf_analyzer.produce_complex_solution(_baseline.truth_table)
    parsimonious_terms = _cf_analyzer.produce_parsimonious_solution(
        _baseline.truth_table, None
    )
    intermediate_terms = _cf_analyzer.produce_intermediate_solution(
        _baseline.truth_table, {}
    )

    # Extend the CounterfactualReport with solution terms (backward-compatible:
    # the frontend CounterfactualReport TypeScript interface only reads the
    # standard fields; extra keys are safely ignored at runtime.)
    _output = _report.model_dump(mode="json")
    _output["complex_terms"] = complex_terms
    _output["parsimonious_terms"] = parsimonious_terms
    _output["intermediate_terms"] = intermediate_terms

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(_output, f, ensure_ascii=False, default=str)


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

    # Extract expected_outcome column from CSV/JSON content and attach to metadata
    if _fmt in ("csv", "json") and config.get("content"):
        try:
            from io import StringIO as _StringIO

            import pandas as _pd

            _df = (
                _pd.read_csv(_StringIO(config["content"]))
                if _fmt == "csv"
                else _pd.read_json(_StringIO(config["content"]))
            )
            if "expected_outcome" in _df.columns:
                for _i, _row in _df.iterrows():
                    if _i < len(entries):
                        entries[_i]["metadata"]["expected_outcome"] = float(
                            _row["expected_outcome"]
                        )
        except Exception as _e:
            print(
                f"[corpus-diag] expected_outcome extraction failed: {_e}",
                file=__import__("sys").stderr,
                flush=True,
            )

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False)


def handle_load_corpus_direct(config_path, output_path):
    """Parse a pre-written corpus file using TextCorpusReader.

    Unlike handle_load_corpus(), this function does NOT read config JSON
    containing the full file content — the worker JS already wrote the content
    to the VFS directly.  ``config_path`` is a JSON with a single key:

    - ``vfsFile``: VFS path to the pre-written corpus file (e.g.
      ``/tmp/sample_cases.csv``).

    This avoids potential encoding/truncation issues when large CSV content
    with Chinese text passes through the JSON.stringify → Python json.load →
    f.write chain.

    Args:
        config_path: VFS path to JSON ``{"vfsFile": "..."}``.
        output_path: VFS path to write the JSON array of
            ``{text_id, text, metadata}`` entries.
    """
    import os as _os

    from experiment_engine.io.readers import TextCorpusReader

    with open(config_path, encoding="utf-8") as f:
        cfg = json.load(f)
    vfs_file_path = cfg["vfsFile"]

    # DIAG: verify the corpus file before pandas reads it
    # Retry loop: Pyodide VFS may need a moment to stabilize after FS.writeFile
    import time as _time

    _size = 0
    _max_retries = 3
    for _attempt in range(_max_retries):
        try:
            _size = _os.path.getsize(vfs_file_path)
            print(
                f"[corpus-diag] pre-read (attempt {_attempt + 1}): {vfs_file_path} size={_size}",
                file=__import__("sys").stderr,
                flush=True,
            )
            if _size > 0:
                break
            if _attempt < _max_retries - 1:
                print(
                    f"[corpus-diag] pre-read (attempt {_attempt + 1}) size=0, retrying...",
                    file=__import__("sys").stderr,
                    flush=True,
                )
                _time.sleep(0.1)
        except OSError as _e:
            print(
                f"[corpus-diag] pre-read stat failed (attempt {_attempt + 1}): {_e}",
                file=__import__("sys").stderr,
                flush=True,
            )
            if _attempt < _max_retries - 1:
                _time.sleep(0.1)
            else:
                raise

    if _size == 0:
        raise RuntimeError(
            f"Corpus file {vfs_file_path} is 0 bytes after {_max_retries} retries — "
            "FS.writeFile did not write the content correctly."
        )

    reader = TextCorpusReader()
    result = reader.read(vfs_file_path)

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

    # Extract expected_outcome column from CSV and attach to metadata
    if vfs_file_path.endswith(".csv"):
        try:
            import pandas as _pd

            _df = _pd.read_csv(vfs_file_path, encoding="utf-8")
            if "expected_outcome" in _df.columns:
                for _i, _row in _df.iterrows():
                    if _i < len(entries):
                        entries[_i]["metadata"]["expected_outcome"] = float(
                            _row["expected_outcome"]
                        )
        except Exception as _e:
            print(
                f"[corpus-diag] expected_outcome extraction failed: {_e}",
                file=__import__("sys").stderr,
                flush=True,
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

    # qca_reporter is excluded from Pyodide deployments (the report/ package
    # is not included in the tar.gz archive). The import is deferred to the
    # 'latex' branch below, where it is wrapped in try/except ImportError.

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
        try:
            from experiment_engine.report.qca_reporter import QCALaTeXReporter
        except ImportError as err:
            raise ImportError(
                "LaTeX export is not available in the browser environment. "
                "Use CSV or JSON export instead."
            ) from err
        _reporter = QCALaTeXReporter()
        out = _reporter.generate(_result)
        mime = "application/x-latex"
    elif fmt == "docx":
        try:
            from experiment_engine.report.docx_reporter import QCADocxReporter
        except ImportError as err:
            raise ImportError(
                "DOCX export is not available in the browser environment. "
                "python-docx must be installed via micropip first."
            ) from err
        _reporter = QCADocxReporter()
        _docx_bytes = _reporter.generate(_result)
        import base64 as _b64

        out = _b64.b64encode(_docx_bytes).decode("ascii")
        mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
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
    if not isinstance(_cs_dict, dict):
        raise TypeError(
            f"condition_set JSON must be a dict, got {type(_cs_dict).__name__}. "
            "Frontend likely passed raw YAML string instead of parsed ConditionSet object."
        )
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

    # ── Validate: all conditions with prototypes must have prototype_embeddings ──
    for _cond in _all_conditions:
        if len(_cond.prototypes) > 0:
            _raw = _raw_conds.get(_cond.name, {})
            _pe = _raw.get("prototype_embeddings")
            if not _pe or len(_pe) == 0:
                raise ValueError(
                    f"Condition '{_cond.name}' has {len(_cond.prototypes)} prototype(s) "
                    f"but no prototype_embeddings. Ensure BERT embeddings are computed "
                    f"before calling handle_embed_calibrate."
                )

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

    # Guard: if _condition_prototypes is empty, raw_scores will be all zeros,
    # which causes DirectCalibration to raise "All raw scores are identical".
    if not _condition_prototypes:
        raise ValueError(
            "No condition prototypes with embeddings found in condition set. "
            "Missing prototype_embeddings in all conditions. "
            "Run BERT embedding computation before calling embed_calibrate."
        )

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


# ─── Multi-Outcome Comparison ────────────────────────────────────────────────


def handle_multi_outcome(analyses_path, output_path):
    """Compare QCA results across multiple outcomes.

    Args:
        analyses_path: VFS path to JSON dict mapping outcome_name →
                       QCAAnalysisResult (serialized as JSON dict).
        output_path: VFS path to write the MultiOutcomeReport JSON.
    """
    from experiment_engine.models import QCAAnalysisResult
    from experiment_engine.qca_engine.advanced.multi_outcome import (
        MultiOutcomeComparison,
    )

    with open(analyses_path, encoding="utf-8") as f:
        _analyses_dict = json.load(f)

    _analyses = {}
    for _name, _result_dict in _analyses_dict.items():
        _analyses[_name] = QCAAnalysisResult(**_result_dict)

    _comparer = MultiOutcomeComparison()
    _report = _comparer.compare(_analyses)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(_report.model_dump(mode="json"), f, ensure_ascii=False, default=str)
