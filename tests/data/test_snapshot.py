import json
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs

import httpx
import pytest

from nyc_housing_rl.data.client import SocrataClient
from nyc_housing_rl.data.snapshot import verify_snapshot, write_snapshot
from nyc_housing_rl.data.sources import DatasetSpec


def _spec() -> DatasetSpec:
    return DatasetSpec(
        name="fixture",
        dataset_id="abcd-1234",
        title="Fixture",
        page_url="https://example.test/d/abcd-1234",
        select=("id",),
        order=("id",),
    )


def test_snapshot_is_manifested_verified_and_immutable(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        offset = int(parse_qs(request.url.query.decode())["$offset"][0])
        rows = [{"id": str(offset)}] if offset == 0 else []
        return httpx.Response(200, content=json.dumps(rows), request=request)

    with SocrataClient(page_size=2, transport=httpx.MockTransport(handler)) as client:
        manifest = write_snapshot(
            client=client,
            spec=_spec(),
            root=tmp_path,
            snapshot_date=date(2026, 7, 6),
        )
        with pytest.raises(FileExistsError):
            write_snapshot(
                client=client,
                spec=_spec(),
                root=tmp_path,
                snapshot_date=date(2026, 7, 6),
            )

    assert manifest.row_count == 1
    verified = verify_snapshot(tmp_path / "2026-07-06" / "fixture")
    assert verified.parts[0].rows == 1


def test_snapshot_detects_tampering(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{"id": "1"}], request=request)

    with SocrataClient(page_size=10, transport=httpx.MockTransport(handler)) as client:
        write_snapshot(
            client=client,
            spec=_spec(),
            root=tmp_path,
            snapshot_date=date(2026, 7, 6),
        )

    part = tmp_path / "2026-07-06" / "fixture" / "part-00000.jsonl"
    part.write_text('{"id":"changed"}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="Checksum mismatch"):
        verify_snapshot(part.parent)
