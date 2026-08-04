"""Flask routes for the local equation calibration evidence viewer."""

from __future__ import annotations

import secrets
from pathlib import Path

from flask import Flask, redirect, render_template, request, url_for

from .evidence import (
    DEFAULT_BATCH_SEED,
    DEFAULT_BATCH_SIZE,
    DEFAULT_FIXED_SEED,
    DEFAULT_OUTPUT_PATH,
    MAX_BATCH_SIZE,
    build_evidence,
)


def _integer_argument(name: str, default: int, minimum: int | None = None, maximum: int | None = None) -> int:
    raw_value = request.args.get(name, str(default)).strip()
    try:
        value = int(raw_value)
    except ValueError as error:
        raise ValueError(f"{name.replace('_', ' ').capitalize()} must be an integer.") from error
    if (minimum is not None and value < minimum) or (maximum is not None and value > maximum):
        raise ValueError(f"{name.replace('_', ' ').capitalize()} must be between {minimum} and {maximum}.")
    return value


def create_app(output_path: Path = DEFAULT_OUTPUT_PATH) -> Flask:
    """Create the deliberately separate local-only viewer application."""
    app = Flask(__name__, template_folder="templates", static_folder="static")

    @app.get("/")
    def calibration_sheet():
        try:
            fixed_seed = _integer_argument("fixed_seed", DEFAULT_FIXED_SEED)
            batch_size = _integer_argument("batch_size", DEFAULT_BATCH_SIZE, 1, MAX_BATCH_SIZE)
            if request.args.get("fresh") == "1":
                return redirect(
                    url_for(
                        "calibration_sheet",
                        fixed_seed=fixed_seed,
                        batch_seed=secrets.randbelow(2**31),
                        batch_size=batch_size,
                    )
                )
            batch_seed = _integer_argument("batch_seed", DEFAULT_BATCH_SEED)
            evidence = build_evidence(fixed_seed, batch_seed, batch_size, output_path)
            fixed_samples = evidence["fixed_sheet"]
            summaries = {
                item["candidate_id"]: item["summary"] for item in evidence["batch_candidates"]
            }
            return render_template(
                "index.html",
                evidence=evidence,
                fixed_samples=fixed_samples,
                summaries=summaries,
                max_batch_size=MAX_BATCH_SIZE,
                form_values={
                    "fixed_seed": fixed_seed,
                    "batch_seed": batch_seed,
                    "batch_size": batch_size,
                },
                error=None,
            )
        except ValueError as error:
            return (
                render_template(
                    "index.html",
                    evidence=None,
                    fixed_samples=[],
                    summaries={},
                    max_batch_size=MAX_BATCH_SIZE,
                    form_values={
                        "fixed_seed": request.args.get("fixed_seed", str(DEFAULT_FIXED_SEED)),
                        "batch_seed": request.args.get("batch_seed", str(DEFAULT_BATCH_SEED)),
                        "batch_size": request.args.get("batch_size", str(DEFAULT_BATCH_SIZE)),
                    },
                    error=str(error),
                ),
                400,
            )

    return app
