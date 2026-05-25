"""Unit tests for keyword dictionary import/export (keyword_io.py)."""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from experiment_engine.models import TextDomain
from experiment_engine.text_calibration.domains import build_default_conditions
from experiment_engine.text_calibration.keyword_io import (
    export_keywords_csv,
    export_keywords_json,
    import_keywords_csv,
    import_keywords_json,
)


class TestImportKeywordsCSV:
    """Tests for import_keywords_csv."""

    @pytest.mark.skip(reason="Keyword IO deprecated — will be removed in Phase 5")
    def test_basic_csv_import(self):
        """Import a simple CSV with two conditions and keywords."""
        csv_content = (
            "condition,keyword,weight,notes\r\n"
            "dissatisfaction,keyword1,1.0,note1\r\n"
            "dissatisfaction,keyword2,0.8,\r\n"
            "trust,trust_keyword,0.9,trust note\r\n"
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", encoding="utf-8", delete=False
        ) as f:
            f.write(csv_content)
            tmp = f.name

        try:
            cs = import_keywords_csv(tmp, domain="dissatisfaction", name="test_cs")
        finally:
            os.unlink(tmp)

        assert cs.name == "test_cs"
        assert cs.domain == TextDomain.DISSATISFACTION
        assert len(cs.conditions) == 2
        assert cs.outcome is None

        # First condition
        c1 = cs.conditions[0]
        assert c1.name == "dissatisfaction"
        assert len(c1.keywords) == 2
        assert c1.keywords[0].pattern == "keyword1"
        assert c1.keywords[0].weight == 1.0
        assert c1.keywords[0].notes == "note1"
        assert c1.keywords[1].pattern == "keyword2"
        assert c1.keywords[1].weight == 0.8
        assert c1.keywords[1].notes == ""

        # Second condition
        c2 = cs.conditions[1]
        assert c2.name == "trust"
        assert len(c2.keywords) == 1
        assert c2.keywords[0].pattern == "trust_keyword"
        assert c2.keywords[0].notes == "trust note"

    @pytest.mark.skip(reason="Keyword IO deprecated — will be removed in Phase 5")
    def test_weight_validation(self):
        """Weight outside [0, 1] raises ValueError."""
        csv_content = "condition,keyword,weight,notes\r\ncond,keyword1,1.5,\r\n"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", encoding="utf-8", delete=False
        ) as f:
            f.write(csv_content)
            tmp = f.name

        try:
            with pytest.raises(ValueError, match="not in \\[0, 1\\]"):
                import_keywords_csv(tmp)
        finally:
            os.unlink(tmp)

    @pytest.mark.skip(reason="Keyword IO deprecated — will be removed in Phase 5")
    def test_duplicate_keyword_rejected(self):
        """Duplicate keyword in same condition raises ValueError."""
        csv_content = (
            "condition,keyword,weight,notes\r\ncond,dup_kw,1.0,\r\ncond,dup_kw,0.5,\r\n"
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", encoding="utf-8", delete=False
        ) as f:
            f.write(csv_content)
            tmp = f.name

        try:
            with pytest.raises(ValueError, match="Duplicate keyword"):
                import_keywords_csv(tmp)
        finally:
            os.unlink(tmp)

    @pytest.mark.skip(reason="Keyword IO deprecated — will be removed in Phase 5")
    def test_missing_columns(self):
        """CSV missing required columns raises ValueError."""
        csv_content = "condition,keyword\r\ncond,kw1\r\n"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", encoding="utf-8", delete=False
        ) as f:
            f.write(csv_content)
            tmp = f.name

        try:
            with pytest.raises(ValueError, match="missing required column"):
                import_keywords_csv(tmp)
        finally:
            os.unlink(tmp)

    @pytest.mark.skip(reason="Keyword IO deprecated — will be removed in Phase 5")
    def test_empty_values_rejected(self):
        """Empty condition or keyword raises ValueError."""
        csv_content = "condition,keyword,weight,notes\r\n  ,kw1,1.0,\r\n"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", encoding="utf-8", delete=False
        ) as f:
            f.write(csv_content)
            tmp = f.name

        try:
            with pytest.raises(ValueError, match="empty condition or keyword"):
                import_keywords_csv(tmp)
        finally:
            os.unlink(tmp)

    @pytest.mark.skip(reason="Keyword IO deprecated — will be removed in Phase 5")
    def test_default_weight_when_missing(self):
        """Weight defaults to 1.0 when not provided but column exists."""
        csv_content = "condition,keyword,weight,notes\r\ncond,kw1,,no weight\r\n"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", encoding="utf-8", delete=False
        ) as f:
            f.write(csv_content)
            tmp = f.name

        try:
            cs = import_keywords_csv(tmp)
        finally:
            os.unlink(tmp)

        assert len(cs.conditions) == 1
        assert cs.conditions[0].keywords[0].weight == 1.0

    @pytest.mark.skip(reason="Keyword IO deprecated — will be removed in Phase 5")
    def test_invalid_weight_string(self):
        """Non-numeric weight raises ValueError."""
        csv_content = "condition,keyword,weight,notes\r\ncond,kw1,abc,\r\n"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", encoding="utf-8", delete=False
        ) as f:
            f.write(csv_content)
            tmp = f.name

        try:
            with pytest.raises(ValueError, match="Invalid weight"):
                import_keywords_csv(tmp)
        finally:
            os.unlink(tmp)


class TestImportKeywordsJSON:
    """Tests for import_keywords_json."""

    @pytest.mark.skip(reason="Keyword IO deprecated — will be removed in Phase 5")
    def test_basic_json_import(self):
        """Import a simple JSON with conditions and keywords."""
        data = {
            "domain": "dissatisfaction",
            "name": "test_import",
            "description": "Test import",
            "conditions": [
                {
                    "name": "cond1",
                    "display_name": "Condition 1",
                    "keywords": [
                        {"keyword": "kw1", "weight": 1.0, "notes": "note1"},
                        {"keyword": "kw2", "weight": 0.8, "scope": "unigram"},
                    ],
                },
                {
                    "name": "cond2",
                    "keywords": [
                        {"keyword": "kw3", "weight": 0.5},
                    ],
                },
            ],
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", encoding="utf-8", delete=False
        ) as f:
            json.dump(data, f)
            tmp = f.name

        try:
            cs = import_keywords_json(tmp)
        finally:
            os.unlink(tmp)

        assert cs.name == "test_import"
        assert cs.description == "Test import"
        assert cs.domain == TextDomain.DISSATISFACTION
        assert len(cs.conditions) == 2
        assert cs.outcome is None

        c1 = cs.conditions[0]
        assert c1.name == "cond1"
        assert c1.display_name == "Condition 1"
        assert len(c1.keywords) == 2
        assert c1.keywords[0].pattern == "kw1"
        assert c1.keywords[0].weight == 1.0
        assert c1.keywords[0].notes == "note1"
        assert c1.keywords[0].scope == "bigram"  # default
        assert c1.keywords[1].pattern == "kw2"
        assert c1.keywords[1].scope == "unigram"

    @pytest.mark.skip(reason="Keyword IO deprecated — will be removed in Phase 5")
    def test_json_with_outcome(self):
        """JSON import with outcome condition."""
        data = {
            "domain": "trust",
            "conditions": [
                {
                    "name": "cond1",
                    "keywords": [{"keyword": "kw1", "weight": 1.0}],
                },
            ],
            "outcome": {
                "name": "outcome_cond",
                "display_name": "Outcome",
                "keywords": [
                    {"keyword": "outcome_kw", "weight": 0.9, "notes": "outcome note"},
                ],
            },
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", encoding="utf-8", delete=False
        ) as f:
            json.dump(data, f)
            tmp = f.name

        try:
            cs = import_keywords_json(tmp)
        finally:
            os.unlink(tmp)

        assert cs.outcome is not None
        assert cs.outcome.name == "outcome_cond"
        assert len(cs.outcome.keywords) == 1
        assert cs.outcome.keywords[0].pattern == "outcome_kw"
        assert cs.outcome.keywords[0].weight == 0.9
        assert cs.outcome.keywords[0].notes == "outcome note"

    @pytest.mark.skip(reason="Keyword IO deprecated — will be removed in Phase 5")
    def test_duplicate_condition_name_rejected(self):
        """Duplicate condition name raises ValueError."""
        data = {
            "conditions": [
                {"name": "same_name", "keywords": [{"keyword": "kw1", "weight": 1.0}]},
                {"name": "same_name", "keywords": [{"keyword": "kw2", "weight": 0.5}]},
            ],
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", encoding="utf-8", delete=False
        ) as f:
            json.dump(data, f)
            tmp = f.name

        try:
            with pytest.raises(ValueError, match="Duplicate condition name"):
                import_keywords_json(tmp)
        finally:
            os.unlink(tmp)

    @pytest.mark.skip(reason="Keyword IO deprecated — will be removed in Phase 5")
    def test_duplicate_keyword_in_condition_rejected(self):
        """Duplicate keyword within a condition raises ValueError."""
        data = {
            "conditions": [
                {
                    "name": "cond",
                    "keywords": [
                        {"keyword": "dup", "weight": 1.0},
                        {"keyword": "dup", "weight": 0.5},
                    ],
                },
            ],
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", encoding="utf-8", delete=False
        ) as f:
            json.dump(data, f)
            tmp = f.name

        try:
            with pytest.raises(ValueError, match="Duplicate keyword"):
                import_keywords_json(tmp)
        finally:
            os.unlink(tmp)

    @pytest.mark.skip(reason="Keyword IO deprecated — will be removed in Phase 5")
    def test_weight_out_of_range_rejected(self):
        """Weight outside [0, 1] raises ValueError."""
        data = {
            "conditions": [
                {
                    "name": "cond",
                    "keywords": [{"keyword": "kw", "weight": 2.0}],
                },
            ],
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", encoding="utf-8", delete=False
        ) as f:
            json.dump(data, f)
            tmp = f.name

        try:
            with pytest.raises(ValueError, match="not in \\[0, 1\\]"):
                import_keywords_json(tmp)
        finally:
            os.unlink(tmp)

    @pytest.mark.skip(reason="Keyword IO deprecated — will be removed in Phase 5")
    def test_missing_condition_name_rejected(self):
        """Condition missing 'name' raises ValueError."""
        data = {
            "conditions": [
                {
                    "display_name": "No Name",
                    "keywords": [{"keyword": "kw", "weight": 1.0}],
                },
            ],
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", encoding="utf-8", delete=False
        ) as f:
            json.dump(data, f)
            tmp = f.name

        try:
            with pytest.raises(ValueError, match="missing 'name'"):
                import_keywords_json(tmp)
        finally:
            os.unlink(tmp)


class TestExportKeywordsCSV:
    """Tests for export_keywords_csv."""

    @pytest.mark.skip(reason="Keyword IO deprecated — will be removed in Phase 5")
    def test_export_csv_roundtrip(self):
        """Export a ConditionSet to CSV and re-import: should match."""
        cs = build_default_conditions(TextDomain.DISSATISFACTION)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", encoding="utf-8", delete=False
        ) as f:
            f.write("")  # placeholder
            tmp = f.name

        try:
            count = export_keywords_csv(cs, tmp)
            assert count > 0

            # Re-import
            cs2 = import_keywords_csv(tmp, domain="dissatisfaction")
        finally:
            os.unlink(tmp)

        # Same number of conditions (outcome becomes a regular condition in CSV)
        original_conditions = len(cs.conditions) + (1 if cs.outcome else 0)
        assert len(cs2.conditions) == original_conditions

        # Verify keywords match
        orig_keywords = set()
        for c in list(cs.conditions) + ([cs.outcome] if cs.outcome else []):
            for kw in c.keywords:
                orig_keywords.add((c.name, kw.pattern, kw.weight))

        imported_keywords = set()
        for c in cs2.conditions:
            for kw in c.keywords:
                imported_keywords.add((c.name, kw.pattern, kw.weight))

        assert orig_keywords == imported_keywords

    @pytest.mark.skip(reason="Keyword IO deprecated — will be removed in Phase 5")
    def test_export_csv_includes_notes(self):
        """CSV export includes notes column."""
        from experiment_engine.models import (
            ConditionDefinition,
            ConditionSet,
            KeywordEntry,
        )

        cs = ConditionSet(
            name="test",
            conditions=[
                ConditionDefinition(
                    name="c1",
                    domain=TextDomain.TRUST,
                    display_name="C1",
                    keywords=[
                        KeywordEntry(pattern="kw1", weight=1.0, notes="important"),
                    ],
                ),
            ],
            domain=TextDomain.TRUST,
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", encoding="utf-8", delete=False
        ) as f:
            f.write("")
            tmp = f.name

        try:
            export_keywords_csv(cs, tmp)
            with open(tmp, encoding="utf-8") as f:
                content = f.read()
        finally:
            os.unlink(tmp)

        assert "condition,keyword,weight,notes" in content
        assert "important" in content


class TestExportKeywordsJSON:
    """Tests for export_keywords_json."""

    @pytest.mark.skip(reason="Keyword IO deprecated — will be removed in Phase 5")
    def test_export_json_roundtrip(self):
        """Export a ConditionSet to JSON and re-import: should match."""
        cs = build_default_conditions(TextDomain.DISSATISFACTION)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", encoding="utf-8", delete=False
        ) as f:
            f.write("{}")
            tmp = f.name

        try:
            export_keywords_json(cs, tmp)
            cs2 = import_keywords_json(tmp)
        finally:
            os.unlink(tmp)

        assert cs2.domain == cs.domain
        assert len(cs2.conditions) == len(cs.conditions)
        assert cs2.outcome is not None

        for c1, c2 in zip(cs.conditions, cs2.conditions, strict=True):
            assert c1.name == c2.name
            assert len(c1.keywords) == len(c2.keywords)
            for kw1, kw2 in zip(c1.keywords, c2.keywords, strict=True):
                assert kw1.pattern == kw2.pattern
                assert kw1.weight == kw2.weight

    @pytest.mark.skip(reason="Keyword IO deprecated — will be removed in Phase 5")
    def test_export_json_without_outcome(self):
        """Export a ConditionSet without outcome."""
        from experiment_engine.models import ConditionDefinition, ConditionSet

        cs = ConditionSet(
            name="no_outcome",
            conditions=[
                ConditionDefinition(
                    name="c1",
                    domain=TextDomain.TRUST,
                    display_name="C1",
                    keywords=[],
                ),
            ],
            domain=TextDomain.TRUST,
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", encoding="utf-8", delete=False
        ) as f:
            f.write("{}")
            tmp = f.name

        try:
            export_keywords_json(cs, tmp)
            with open(tmp, encoding="utf-8") as f:
                data = json.load(f)
        finally:
            os.unlink(tmp)

        assert "outcome" not in data
        assert len(data["conditions"]) == 1
        assert data["conditions"][0]["name"] == "c1"
