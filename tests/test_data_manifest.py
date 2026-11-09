import pytest

from src.data_manifest import (
    CSV_SOURCES,
    build_manifest,
    parse_dates,
    verify_manifest,
)


@pytest.fixture
def sample_snapshot(tmp_path):
    """Искусственные CSV без использования реальных данных."""
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)

    for filename in CSV_SOURCES:
        (raw_dir / filename).write_text(
            "id,value\n1,alpha\n2,beta\n",
            encoding="utf-8",
        )

    return tmp_path


def test_valid_manifest(sample_snapshot):
    manifest = build_manifest(sample_snapshot)

    assert len(manifest["files"]) == 8
    assert verify_manifest(sample_snapshot, manifest) == []


def test_detect_modified_content(sample_snapshot):
    manifest = build_manifest(sample_snapshot)

    path = (
        sample_snapshot
        / "data/raw/first_questions_2023.csv"
    )

    # Изменяем содержимое без изменения размера файла
    content = path.read_text(encoding="utf-8")
    path.write_text(
        content.replace("alpha", "bravo"),
        encoding="utf-8",
    )

    errors = verify_manifest(sample_snapshot, manifest)

    assert any("sha256" in error for error in errors)


def test_detect_changed_row_count(sample_snapshot):
    manifest = build_manifest(sample_snapshot)

    path = (
        sample_snapshot
        / "data/raw/posts_activity_2023.csv"
    )

    with path.open("a", encoding="utf-8") as file:
        file.write("3,gamma\n")

    errors = verify_manifest(sample_snapshot, manifest)

    assert any("rows" in error for error in errors)


def test_detect_missing_csv(sample_snapshot):
    manifest = build_manifest(sample_snapshot)

    path = (
        sample_snapshot
        / "data/raw/comments_2023_h1.csv"
    )
    path.unlink()

    errors = verify_manifest(sample_snapshot, manifest)

    assert any(
        "comments_2023_h1.csv" in error
        for error in errors
    )


def test_detect_missing_manifest_entry(sample_snapshot):
    manifest = build_manifest(sample_snapshot)
    manifest["files"].pop()

    errors = verify_manifest(sample_snapshot, manifest)

    assert any("Нет записи" in error for error in errors)


def test_extraction_date(sample_snapshot):
    filename = "first_questions_2023.csv"
    dates = parse_dates([f"{filename}=2026-10-15"])

    manifest = build_manifest(sample_snapshot, dates)

    assert manifest["files"][0]["extracted_on"] == (
        "2026-10-15"
    )


def test_invalid_extraction_date():
    with pytest.raises(ValueError, match="Некорректная дата"):
        parse_dates([
            "first_questions_2023.csv=2026-02-30"
        ])