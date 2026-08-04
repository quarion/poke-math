"""Focused tests for the local equation calibration evidence viewer."""

import json
from fractions import Fraction

import sympy as sp
from tools.equation_calibration import app as calibration_app
from tools.equation_calibration import evidence


def _candidate(candidate_id: str, params: dict) -> dict:
    return {
        "id": candidate_id,
        "name": candidate_id.title(),
        "difficulty": 1,
        "capability_description": f"Current capability for {candidate_id}.",
        "params": params,
    }


def test_fixed_seed_sheet_is_deterministic_and_does_not_mutate_params():
    candidates = [
        _candidate(
            "addition",
            {
                "type": "basic_math",
                "operations": ["+"],
                "max_value": 10,
                "allow_decimals": False,
                "elements": 2,
            },
        )
    ]

    first_sheet = evidence.build_fixed_sheet(candidates, fixed_seed=1234)
    second_sheet = evidence.build_fixed_sheet(candidates, fixed_seed=1234)

    assert first_sheet == second_sheet
    assert "random_seed" not in candidates[0]["params"]


def test_batch_continues_after_generation_error_and_summarizes_results():
    candidates = [
        _candidate("working", {"type": "basic_math", "operations": ["+"], "max_value": 10}),
        _candidate("broken", {"type": "not-supported"}),
    ]

    batch_candidates = evidence.build_batch(candidates, batch_seed=9, batch_size=5)

    working, broken = batch_candidates
    assert working["summary"]["requested_count"] == 5
    assert working["summary"]["success_count"] == 5
    assert working["summary"]["unique_count"] + working["summary"]["duplicate_count"] == 5
    assert broken["summary"]["failure_count"] == 5
    assert all(sample["status"] == "error" for sample in broken["samples"])
    assert {tail["reason"] for tail in broken["summary"]["selected_tail_cases"]} == {"failure"}
    assert len(broken["summary"]["selected_tail_cases"]) == 3


def test_evidence_json_is_portable_and_saved(tmp_path):
    output_path = tmp_path / "latest.json"
    candidate = _candidate(
        "addition",
        {"type": "basic_math", "operations": ["+"], "max_value": 10, "elements": 2},
    )

    result = evidence.build_evidence(
        fixed_seed=12,
        batch_seed=13,
        batch_size=1,
        output_path=output_path,
        candidates=[candidate],
    )
    saved = json.loads(output_path.read_text(encoding="utf-8"))

    assert saved["schema_version"] == evidence.EVIDENCE_SCHEMA_VERSION
    assert saved["fixed_seed"] == 12
    assert saved["batch_candidates"][0]["samples"][0]["seed"] == result["batch_candidates"][0]["samples"][0]["seed"]
    assert evidence.json_value(Fraction(2, 3)) == {"type": "fraction", "numerator": 2, "denominator": 3}
    assert evidence.json_value(sp.Rational(2, 3)) == {
        "type": "sympy_rational",
        "numerator": 2,
        "denominator": 3,
    }


def test_local_route_renders_scan_sheet_and_saved_evidence_path(monkeypatch, tmp_path):
    sample = {
        "candidate_id": "addition",
        "candidate_order": 1,
        "candidate_name": "Beginner",
        "capability_description": "Solve a one-step addition equation.",
        "seed": 44,
        "status": "success",
        "displayed_equations": ["x = 2 + 3"],
        "answer": {"x": 5},
        "measurements": {
            "equation_count": 1,
            "variable_count": 1,
            "operation_count": 1,
            "operators_present": ["+"],
            "exercise_signature": "abc123",
        },
        "diagnostics": {"symbolic_solution_satisfies_equations": True},
    }
    summary = {
        "requested_count": 2,
        "success_count": 2,
        "failure_count": 0,
        "unique_count": 2,
        "duplicate_count": 0,
        "diagnostic_violation_count": 0,
        "negative_solution_count": 0,
        "non_integer_solution_count": 0,
        "property_distributions": {
            "equation_count": {"min": 1, "max": 1},
            "variable_count": {"min": 1, "max": 1},
            "operation_count": {"min": 1, "max": 1},
        },
        "selected_tail_cases": [],
    }
    monkeypatch.setattr(
        calibration_app,
        "build_evidence",
        lambda fixed_seed, batch_seed, batch_size, output_path: {
            "fixed_seed": fixed_seed,
            "batch_seed": batch_seed,
            "batch_size": batch_size,
            "saved_evidence_path": "artifacts/equation-calibration/latest.json",
            "fixed_sheet": [sample],
            "batch_candidates": [{"candidate_id": "addition", "summary": summary}],
        },
    )

    response = calibration_app.create_app(tmp_path / "latest.json").test_client().get(
        "/?fixed_seed=44&batch_seed=55&batch_size=2"
    )

    assert response.status_code == 200
    assert b"Equation calibration viewer" in response.data
    assert b"Solve a one-step addition equation." in response.data
    assert b"artifacts/equation-calibration/latest.json" in response.data


def test_local_route_rejects_out_of_range_batch_size(tmp_path):
    response = calibration_app.create_app(tmp_path / "latest.json").test_client().get("/?batch_size=101")

    assert response.status_code == 400
    assert b"Batch size must be between 1 and 100." in response.data
    assert response.data.count(b'value="20260804"') == 2


def test_fresh_batch_redirects_to_a_reproducible_canonical_url(monkeypatch, tmp_path):
    generated_runs = []
    monkeypatch.setattr(calibration_app.secrets, "randbelow", lambda upper_bound: 987654321)
    monkeypatch.setattr(
        calibration_app,
        "build_evidence",
        lambda fixed_seed, batch_seed, batch_size, output_path: generated_runs.append(
            (fixed_seed, batch_seed, batch_size)
        )
        or {
            "fixed_seed": fixed_seed,
            "batch_seed": batch_seed,
            "batch_size": batch_size,
            "saved_evidence_path": "artifacts/equation-calibration/latest.json",
            "fixed_sheet": [],
            "batch_candidates": [],
        },
    )
    client = calibration_app.create_app(tmp_path / "latest.json").test_client()

    response = client.get("/?fixed_seed=44&batch_seed=55&batch_size=2&fresh=1")

    assert response.status_code == 302
    assert response.headers["Location"] == "/?fixed_seed=44&batch_seed=987654321&batch_size=2"
    assert client.get(response.headers["Location"]).status_code == 200
    assert client.get(response.headers["Location"]).status_code == 200
    assert generated_runs == [(44, 987654321, 2), (44, 987654321, 2)]
