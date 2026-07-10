"""Immutable raw snapshots with request and checksum manifests."""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from nyc_housing_rl.data.client import SocrataClient
from nyc_housing_rl.data.sources import DatasetSpec


@dataclass(frozen=True, slots=True)
class SnapshotPart:
    file: str
    query_index: int
    page_index: int
    rows: int
    sha256: str


@dataclass(frozen=True, slots=True)
class SnapshotManifest:
    format_version: int
    source_name: str
    dataset_id: str
    source_url: str
    snapshot_date: str
    retrieved_at: str
    queries: tuple[dict[str, str], ...]
    row_count: int
    parts: tuple[SnapshotPart, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def snapshot_directory(root: Path, snapshot_date: date, source_name: str) -> Path:
    return root / snapshot_date.isoformat() / source_name


def write_snapshot(
    *,
    client: SocrataClient,
    spec: DatasetSpec,
    root: Path,
    snapshot_date: date,
    queries: Sequence[Mapping[str, str]] | None = None,
    force: bool = False,
) -> SnapshotManifest:
    """Write a source snapshot atomically enough to reject partial reuse.

    Existing snapshots are immutable unless ``force`` is explicit. Each JSONL part
    is written to a temporary file, fsynced, and renamed before the manifest.
    """

    destination = snapshot_directory(root, snapshot_date, spec.name)
    manifest_path = destination / "manifest.json"
    if manifest_path.exists() and not force:
        raise FileExistsError(f"Snapshot already exists: {manifest_path}")
    destination.mkdir(parents=True, exist_ok=True)

    normalized_queries = tuple(dict(query) for query in (queries or (spec.query(),)))
    parts: list[SnapshotPart] = []
    total_rows = 0
    part_number = 0
    for query_index, query in enumerate(normalized_queries):
        for page_index, rows in enumerate(client.iter_pages(spec.dataset_id, query)):
            body = "".join(
                json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows
            ).encode("utf-8")
            filename = f"part-{part_number:05d}.jsonl"
            _atomic_write(destination / filename, body)
            parts.append(
                SnapshotPart(
                    file=filename,
                    query_index=query_index,
                    page_index=page_index,
                    rows=len(rows),
                    sha256=hashlib.sha256(body).hexdigest(),
                )
            )
            total_rows += len(rows)
            part_number += 1

    manifest = SnapshotManifest(
        format_version=1,
        source_name=spec.name,
        dataset_id=spec.dataset_id,
        source_url=spec.page_url,
        snapshot_date=snapshot_date.isoformat(),
        retrieved_at=datetime.now(UTC).isoformat(),
        queries=normalized_queries,
        row_count=total_rows,
        parts=tuple(parts),
    )
    manifest_body = (json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n").encode()
    _atomic_write(manifest_path, manifest_body)
    return manifest


def load_manifest(path: Path) -> SnapshotManifest:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["queries"] = tuple(payload["queries"])
    payload["parts"] = tuple(SnapshotPart(**part) for part in payload["parts"])
    return SnapshotManifest(**payload)


def verify_snapshot(directory: Path) -> SnapshotManifest:
    manifest = load_manifest(directory / "manifest.json")
    observed_rows = 0
    for part in manifest.parts:
        body = (directory / part.file).read_bytes()
        if hashlib.sha256(body).hexdigest() != part.sha256:
            raise ValueError(f"Checksum mismatch: {part.file}")
        rows = sum(1 for line in body.splitlines() if line)
        if rows != part.rows:
            raise ValueError(f"Row count mismatch: {part.file}")
        observed_rows += rows
    if observed_rows != manifest.row_count:
        raise ValueError("Snapshot row count does not match its manifest")
    return manifest


def read_snapshot_rows(directory: Path) -> list[dict[str, Any]]:
    manifest = verify_snapshot(directory)
    rows: list[dict[str, Any]] = []
    for part in manifest.parts:
        with (directory / part.file).open(encoding="utf-8") as handle:
            rows.extend(json.loads(line) for line in handle if line.strip())
    return rows


def _atomic_write(path: Path, body: bytes) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as handle:
        handle.write(body)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)
