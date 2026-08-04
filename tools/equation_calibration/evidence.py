"""Generate portable, reproducible evidence for the equation calibration viewer."""

from __future__ import annotations

import hashlib
import json
import random
from collections import Counter
from datetime import UTC, datetime
from fractions import Fraction
from pathlib import Path
from typing import Any

import sympy as sp

from src.app.equations.equations_generator_v2 import DynamicQuizV2, EquationsGeneratorV2

EVIDENCE_SCHEMA_VERSION = 1
DEFAULT_FIXED_SEED = 20260804
DEFAULT_BATCH_SEED = 20260804
DEFAULT_BATCH_SIZE = 12
MAX_BATCH_SIZE = 100
MAX_SELECTED_TAIL_CASES_PER_REASON = 3
REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "src" / "data" / "equation_difficulties_v2.json"
DEFAULT_OUTPUT_PATH = REPO_ROOT / "artifacts" / "equation-calibration" / "latest.json"
CONFIG_SOURCE = "src/data/equation_difficulties_v2.json"


def load_candidates(config_path: Path = CONFIG_PATH) -> list[dict[str, Any]]:
    """Load the ordered equation candidates without altering their configuration."""
    with config_path.open(encoding="utf-8") as config_file:
        candidates = json.load(config_file)
    if not isinstance(candidates, list):
        raise ValueError("Equation difficulty configuration must be a list.")
    return candidates


def json_value(value: Any) -> Any:
    """Convert generator and SymPy values into JSON-portable equivalents."""
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, Fraction):
        return {"type": "fraction", "numerator": value.numerator, "denominator": value.denominator}
    if isinstance(value, sp.Basic):
        if value.is_Integer:
            return int(value)
        if value.is_Rational:
            return {
                "type": "sympy_rational",
                "numerator": int(value.p),
                "denominator": int(value.q),
            }
        if value.is_Float:
            return float(value)
        return {"type": "sympy", "expression": str(value)}
    if isinstance(value, dict):
        return {str(key): json_value(item) for key, item in value.items()}
    if isinstance(value, list | tuple | set):
        return [json_value(item) for item in value]
    return str(value)


def _numeric_value(value: Any) -> float | None:
    """Return a numeric value when it can be compared safely."""
    if isinstance(value, Fraction):
        return float(value)
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, sp.Number):
        return float(value)
    return None


def _equation_symbols(quiz: DynamicQuizV2) -> set[str]:
    symbols: set[str] = set()
    for equation in quiz.equations:
        symbolic = equation.symbolic
        if isinstance(symbolic, sp.Basic):
            symbols.update(str(symbol) for symbol in symbolic.free_symbols)
    return symbols


def _operator_counts(equations: list[str]) -> dict[str, int]:
    return {operator: sum(equation.count(operator) for equation in equations) for operator in "+-*/"}


def _signature(equations: list[str], answer: dict[str, Any]) -> str:
    stable_value = json.dumps({"equations": equations, "answer": answer}, sort_keys=True)
    return hashlib.sha256(stable_value.encode("utf-8")).hexdigest()[:16]


def _diagnostics(quiz: DynamicQuizV2) -> dict[str, Any]:
    equation_checks: list[dict[str, Any]] = []
    violations = 0
    for index, equation in enumerate(quiz.equations, start=1):
        try:
            symbolic = equation.symbolic
            if not isinstance(symbolic, sp.Equality):
                raise TypeError("stored symbolic equation is not a SymPy Equality")
            difference = sp.simplify((symbolic.lhs - symbolic.rhs).subs(quiz.solution.symbolic))
            satisfied = difference == 0 or bool(difference.equals(0))
            if not satisfied:
                violations += 1
            equation_checks.append(
                {
                    "equation_index": index,
                    "satisfied": satisfied,
                    "residual": json_value(difference),
                }
            )
        except Exception as error:  # Evidence collection must not stop a batch.
            violations += 1
            equation_checks.append(
                {"equation_index": index, "satisfied": False, "error": f"{type(error).__name__}: {error}"}
            )
    return {
        "symbolic_solution_satisfies_equations": violations == 0,
        "symbolic_violation_count": violations,
        "equation_checks": equation_checks,
        "formatted_symbolic_comparison": {
            "status": "not_attempted",
            "reason": "Formatted equations are display strings and are not parsed by this viewer.",
        },
    }


def measure_quiz(quiz: DynamicQuizV2) -> tuple[dict[str, Any], dict[str, Any]]:
    """Extract small, explainable structural measurements and diagnostics from a quiz."""
    equations = [equation.formatted for equation in quiz.equations]
    answer = json_value(quiz.solution.human_readable)
    numeric_solutions = [value for value in quiz.solution.human_readable.values()]
    numeric_values = [_numeric_value(value) for value in numeric_solutions]
    operator_counts = _operator_counts(equations)
    measurements = {
        "equation_count": len(equations),
        "variable_count": len(_equation_symbols(quiz) or quiz.solution.human_readable),
        "operation_count": sum(operator_counts.values()),
        "operator_counts": operator_counts,
        "operators_present": [operator for operator, count in operator_counts.items() if count],
        "all_solutions_integer": bool(numeric_values)
        and all(value is not None and value.is_integer() for value in numeric_values),
        "has_non_integer_solution": any(
            value is not None and not value.is_integer() for value in numeric_values
        ),
        "has_negative_solution": any(
            value is not None and value < 0 for value in numeric_values
        ),
        "exercise_signature": _signature(equations, answer),
    }
    return measurements, _diagnostics(quiz)


def generate_sample(candidate: dict[str, Any], order: int, seed: int) -> dict[str, Any]:
    """Generate one sample, retaining an error record instead of raising to the caller."""
    params = dict(candidate["params"])
    params["random_seed"] = seed
    sample: dict[str, Any] = {
        "candidate_id": candidate["id"],
        "candidate_order": order,
        "candidate_name": candidate["name"],
        "capability_description": candidate.get("capability_description", "No description configured."),
        "seed": seed,
        "config_params": json_value(params),
    }
    try:
        quiz = EquationsGeneratorV2().generate_equations(params)
        measurements, diagnostics = measure_quiz(quiz)
        sample.update(
            {
                "status": "success",
                "displayed_equations": [equation.formatted for equation in quiz.equations],
                "symbolic_equations": [str(equation.symbolic) for equation in quiz.equations],
                "answer": json_value(quiz.solution.human_readable),
                "measurements": measurements,
                "diagnostics": diagnostics,
            }
        )
    except Exception as error:  # Generation failures are evidence, not a failed viewer run.
        sample.update({"status": "error", "error": f"{type(error).__name__}: {error}"})
    return sample


def build_fixed_sheet(candidates: list[dict[str, Any]], fixed_seed: int) -> list[dict[str, Any]]:
    """Generate one same-seed sample for each candidate in configured order."""
    return [generate_sample(candidate, order, fixed_seed) for order, candidate in enumerate(candidates, start=1)]


def _property_distribution(samples: list[dict[str, Any]], property_name: str) -> dict[str, Any]:
    values = [sample["measurements"][property_name] for sample in samples if sample["status"] == "success"]
    return {
        "min": min(values) if values else None,
        "max": max(values) if values else None,
        "counts": {str(value): count for value, count in sorted(Counter(values).items())},
    }


def _tail_case(reason: str, sample: dict[str, Any]) -> dict[str, Any]:
    return {
        "reason": reason,
        "sample_index": sample["sample_index"],
        "seed": sample["seed"],
        "exercise_signature": sample.get("measurements", {}).get("exercise_signature"),
        "displayed_equations": sample.get("displayed_equations", []),
        "answer": sample.get("answer"),
        "measurements": sample.get("measurements"),
        "diagnostics": sample.get("diagnostics"),
        "error": sample.get("error"),
    }


def summarize_batch(samples: list[dict[str, Any]], requested: int) -> dict[str, Any]:
    """Summarize transparent structural properties, failures, and reviewable tail cases."""
    successful = [sample for sample in samples if sample["status"] == "success"]
    failures = [sample for sample in samples if sample["status"] == "error"]
    signatures = [sample["measurements"]["exercise_signature"] for sample in successful]
    seen: set[str] = set()
    duplicate_samples: list[dict[str, Any]] = []
    for sample in successful:
        signature = sample["measurements"]["exercise_signature"]
        if signature in seen:
            duplicate_samples.append(sample)
        seen.add(signature)
    diagnostic_violations = [
        sample
        for sample in successful
        if sample["diagnostics"]["symbolic_violation_count"] > 0
    ]
    def structural_key(sample: dict[str, Any]) -> tuple[int, int, int]:
        return (
            sample["measurements"]["equation_count"],
            sample["measurements"]["variable_count"],
            sample["measurements"]["operation_count"],
        )
    tail_cases = [
        _tail_case("failure", sample) for sample in failures[:MAX_SELECTED_TAIL_CASES_PER_REASON]
    ]
    tail_cases.extend(
        _tail_case("diagnostic_violation", sample)
        for sample in diagnostic_violations[:MAX_SELECTED_TAIL_CASES_PER_REASON]
    )
    tail_cases.extend(
        _tail_case("duplicate", sample)
        for sample in duplicate_samples[:MAX_SELECTED_TAIL_CASES_PER_REASON]
    )
    if successful:
        tail_cases.append(_tail_case("minimum_structural_case", min(successful, key=structural_key)))
        tail_cases.append(_tail_case("maximum_structural_case", max(successful, key=structural_key)))
    return {
        "requested_count": requested,
        "success_count": len(successful),
        "failure_count": len(failures),
        "unique_count": len(set(signatures)),
        "duplicate_count": len(duplicate_samples),
        "diagnostic_violation_count": len(diagnostic_violations),
        "negative_solution_count": sum(
            sample["measurements"]["has_negative_solution"] for sample in successful
        ),
        "non_integer_solution_count": sum(
            sample["measurements"]["has_non_integer_solution"] for sample in successful
        ),
        "property_distributions": {
            name: _property_distribution(successful, name)
            for name in ("equation_count", "variable_count", "operation_count")
        },
        "selected_tail_cases": tail_cases,
    }


def build_batch(candidates: list[dict[str, Any]], batch_seed: int, batch_size: int) -> list[dict[str, Any]]:
    """Generate a deterministic batch for every candidate, recording every individual result."""
    seed_stream = random.Random(batch_seed)
    batch_candidates: list[dict[str, Any]] = []
    for order, candidate in enumerate(candidates, start=1):
        samples = []
        for sample_index in range(1, batch_size + 1):
            sample = generate_sample(candidate, order, seed_stream.randrange(0, 2**31))
            sample["sample_index"] = sample_index
            samples.append(sample)
        batch_candidates.append(
            {
                "candidate_id": candidate["id"],
                "candidate_order": order,
                "candidate_name": candidate["name"],
                "capability_description": candidate.get("capability_description", "No description configured."),
                "samples": samples,
                "summary": summarize_batch(samples, batch_size),
            }
        )
    return batch_candidates


def write_evidence(evidence: dict[str, Any], output_path: Path = DEFAULT_OUTPUT_PATH) -> Path:
    """Persist the complete latest evidence document as portable JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(json_value(evidence), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def build_evidence(
    fixed_seed: int = DEFAULT_FIXED_SEED,
    batch_seed: int = DEFAULT_BATCH_SEED,
    batch_size: int = DEFAULT_BATCH_SIZE,
    output_path: Path = DEFAULT_OUTPUT_PATH,
    candidates: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build and save all fixed and batch evidence for one viewer request."""
    if not 1 <= batch_size <= MAX_BATCH_SIZE:
        raise ValueError(f"Batch size must be between 1 and {MAX_BATCH_SIZE}.")
    candidates = candidates if candidates is not None else load_candidates()
    evidence = {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
        "config_source": CONFIG_SOURCE,
        "fixed_seed": fixed_seed,
        "batch_seed": batch_seed,
        "batch_size": batch_size,
        "fixed_sheet": build_fixed_sheet(candidates, fixed_seed),
        "batch_candidates": build_batch(candidates, batch_seed, batch_size),
    }
    evidence["saved_evidence_path"] = (
        output_path.relative_to(REPO_ROOT).as_posix()
        if output_path.is_relative_to(REPO_ROOT)
        else str(output_path)
    )
    write_evidence(evidence, output_path)
    return evidence
