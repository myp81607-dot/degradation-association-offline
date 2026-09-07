"""Load and merge Prometheus matrix responses from JSON or text files."""

from __future__ import annotations

import json
import math
from collections import defaultdict
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from .series import Sample, SeriesDataError, SeriesId, TimeSeries


class OfflineInputError(ValueError):
    """Offline input cannot be interpreted as Prometheus matrix data."""


def _input_files(paths: Iterable[Path]) -> list[Path]:
    files: list[Path] = []
    for raw_path in paths:
        path = Path(raw_path).expanduser()
        if path.is_dir():
            files.extend(
                item
                for item in sorted(path.rglob("*"))
                if item.is_file() and item.suffix.lower() in {".json", ".txt"}
            )
        elif path.is_file():
            files.append(path)
        else:
            raise OfflineInputError(f"input path does not exist: {path}")
    if not files:
        raise OfflineInputError("no .json or .txt input files were found")
    return files


def _matrix_entries(payload: Any, *, source: Path) -> list[Mapping[str, Any]]:
    if isinstance(payload, list):
        if all(isinstance(item, Mapping) and "metric" in item for item in payload):
            return list(payload)
        entries: list[Mapping[str, Any]] = []
        for item in payload:
            entries.extend(_matrix_entries(item, source=source))
        return entries
    if not isinstance(payload, Mapping):
        raise OfflineInputError(f"{source}: expected a JSON object or array")

    if "series" in payload:
        return _matrix_entries(payload["series"], source=source)
    if "data" in payload:
        data = payload["data"]
        if not isinstance(data, Mapping):
            raise OfflineInputError(f"{source}: data must be an object")
        result_type = data.get("resultType")
        if result_type is not None and result_type != "matrix":
            raise OfflineInputError(
                f"{source}: expected Prometheus matrix data, got {result_type!r}"
            )
        return _matrix_entries(data.get("result"), source=source)
    if "result" in payload:
        return _matrix_entries(payload["result"], source=source)
    if "metric" in payload:
        return [payload]
    raise OfflineInputError(f"{source}: no Prometheus matrix result was found")


def _samples(entry: Mapping[str, Any], *, source: Path) -> list[Sample]:
    raw_values = entry.get("values")
    if raw_values is None and "value" in entry:
        raw_values = [entry["value"]]
    if not isinstance(raw_values, list):
        raise OfflineInputError(f"{source}: series values must be an array")
    samples: list[Sample] = []
    for raw in raw_values:
        if not isinstance(raw, (list, tuple)) or len(raw) != 2:
            raise OfflineInputError(
                f"{source}: every sample must be [timestamp, value]"
            )
        try:
            timestamp = float(raw[0])
            value = float(raw[1])
        except (TypeError, ValueError, OverflowError):
            continue
        if math.isfinite(timestamp) and math.isfinite(value):
            samples.append(Sample(timestamp, value))
    return samples


def load_time_series(paths: Iterable[Path]) -> tuple[TimeSeries, ...]:
    """Read files recursively and merge samples by concrete labeled series."""

    merged: dict[SeriesId, dict[float, float]] = defaultdict(dict)
    for path in _input_files(paths):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise OfflineInputError(f"cannot read JSON from {path}: {exc}") from exc
        for entry in _matrix_entries(payload, source=path):
            metric = entry.get("metric")
            if not isinstance(metric, Mapping):
                raise OfflineInputError(f"{path}: series metric must be an object")
            try:
                identity = SeriesId.from_label_set(metric)
            except SeriesDataError as exc:
                raise OfflineInputError(f"{path}: {exc}") from exc
            for sample in _samples(entry, source=path):
                merged[identity][sample.timestamp] = sample.value

    return tuple(
        TimeSeries(
            identity=identity,
            samples=tuple(
                Sample(timestamp, value) for timestamp, value in sorted(samples.items())
            ),
        )
        for identity, samples in sorted(merged.items())
        if samples
    )


__all__ = ["OfflineInputError", "load_time_series"]
