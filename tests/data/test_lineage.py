from pathlib import Path

from nyc_housing_rl.data.lineage import sha256_file


def test_sha256_file_is_content_addressed(tmp_path: Path) -> None:
    path = tmp_path / "artifact.txt"
    path.write_text("civic inspection\n", encoding="utf-8")
    first = sha256_file(path)
    path.write_text("civic inspection changed\n", encoding="utf-8")
    assert sha256_file(path) != first
