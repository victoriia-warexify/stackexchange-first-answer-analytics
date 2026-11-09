import argparse
import csv
import hashlib
import json

from datetime import date, datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data_manifest.json"

CSV_SOURCES = {
    "first_questions_2023.csv":
        "sql/extraction/06_first_question_users_2023.sql",
    "answers_to_2023_questions.csv":
        "sql/extraction/07_answers_to_2023_questions.sql",
    "posts_activity_2023.csv":
        "sql/extraction/09_posts_activity_2023.sql",
    "comments_2023_h1.csv":
        "sql/extraction/11_comments_activity_2023_h1.sql",
    "comments_2023_h2.csv":
        "sql/extraction/12_comments_activity_2023_h2.sql",
    "comments_2024_jan.csv":
        "sql/extraction/13_comments_activity_2024_jan.sql",
    "user_registration_2023.csv":
        "sql/extraction/14_user_registration_2023.sql",
    "initial_question_metadata_2023.csv":
        "sql/extraction/15_initial_question_metadata_2023.sql",
}


def csv_stats(path: Path) -> dict:
    """Подсчитать строки и SHA-256 оригинального CSV."""
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(
            lambda: file.read(1024 * 1024), b""
        ):
            digest.update(chunk)

    with path.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        reader = csv.reader(file)
        header = next(reader, None)

        if not header or not any(header):
            raise ValueError(f"CSV без заголовка: {path}")

        rows = sum(1 for _ in reader)

    return {
        "rows": rows,
        "size_bytes": path.stat().st_size,
        "sha256": digest.hexdigest(),
    }


def build_manifest(
    root: Path,
    extraction_dates: dict[str, str] | None = None,
) -> dict:
    """Сформировать манифест исходных выгрузок."""
    extraction_dates = extraction_dates or {}
    files = []

    for filename, query in CSV_SOURCES.items():
        path = root / "data" / "raw" / filename

        files.append({
            "filename": filename,
            "path": f"data/raw/{filename}",
            "query": query,
            "extracted_on": extraction_dates.get(filename),
            **csv_stats(path),
        })

    return {
        "schema_version": 1,
        "source": "Stack Exchange Data Explorer",
        "site": "Cross Validated",
        "manifest_generated_at_utc": (
            datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
        ),
        "files": files,
    }


def verify_manifest(root: Path, manifest: dict) -> list[str]:
    """Вернуть список расхождений с манифестом."""
    errors = []

    if manifest.get("schema_version") != 1:
        errors.append("Неподдерживаемая версия манифеста")

    entries = manifest.get("files")

    if not isinstance(entries, list):
        return ["Поле files должно быть списком"]

    indexed = {}

    for entry in entries:
        if not isinstance(entry, dict):
            errors.append("Некорректная запись в files")
            continue

        name = entry.get("filename")

        if name not in CSV_SOURCES:
            errors.append(f"Неизвестный CSV: {name}")
        elif name in indexed:
            errors.append(f"Дублирующаяся запись: {name}")
        else:
            indexed[name] = entry

    for filename, query in CSV_SOURCES.items():
        if filename not in indexed:
            errors.append(f"Нет записи: {filename}")
            continue

        entry = indexed[filename]
        expected_path = f"data/raw/{filename}"

        if entry.get("path") != expected_path:
            errors.append(f"{filename}: неверный путь")

        if entry.get("query") != query:
            errors.append(f"{filename}: изменён источник SQL")

        path = root / expected_path

        try:
            actual = csv_stats(path)
        except (
            OSError, UnicodeError, csv.Error, ValueError
        ) as exc:
            errors.append(f"{filename}: {exc}")
            continue

        for key in ("rows", "size_bytes", "sha256"):
            if entry.get(key) != actual[key]:
                errors.append(
                    f"{filename}: {key} не совпадает "
                    f"(ожидалось {entry.get(key)}, "
                    f"получено {actual[key]})"
                )

    return errors


def parse_dates(values: list[str]) -> dict[str, str]:
    """Разобрать даты подтверждённых выгрузок."""
    result = {}

    for value in values:
        filename, separator, day = value.partition("=")

        if not separator or filename not in CSV_SOURCES:
            raise ValueError(
                f"Используй формат filename.csv=YYYY-MM-DD: {value}"
            )

        if filename in result:
            raise ValueError(f"Повторная дата: {filename}")

        try:
            if date.fromisoformat(day).isoformat() != day:
                raise ValueError
        except ValueError:
            raise ValueError(
                f"Некорректная дата для {filename}: {day}"
            ) from None

        result[filename] = day

    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command", choices=["generate", "verify"]
    )
    parser.add_argument(
        "--date",
        action="append",
        default=[],
        metavar="CSV=YYYY-MM-DD",
        help="Известная дата конкретной выгрузки",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Явно разрешить перезапись манифеста",
    )
    args = parser.parse_args()

    if args.command == "generate":
        if MANIFEST_PATH.exists() and not args.overwrite:
            parser.error(
                "Манифест уже существует. "
                "Для замены используй --overwrite."
            )

        try:
            dates = parse_dates(args.date)
            manifest = build_manifest(ROOT, dates)
        except (OSError, UnicodeError, csv.Error, ValueError) as exc:
            parser.exit(1, f"Ошибка: {exc}\n")

        MANIFEST_PATH.write_text(
            json.dumps(
                manifest,
                ensure_ascii=False,
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )

        print(
            f"Манифест создан: {MANIFEST_PATH.name}"
        )
        print(f"CSV-файлов: {len(manifest['files'])}")

    else:
        if args.date or args.overwrite:
            parser.error(
                "--date и --overwrite доступны только для generate"
            )

        try:
            manifest = json.loads(
                MANIFEST_PATH.read_text(encoding="utf-8")
            )
            errors = verify_manifest(ROOT, manifest)
        except (OSError, ValueError, TypeError) as exc:
            parser.exit(1, f"Ошибка: {exc}\n")

        if errors:
            print("Проверка манифеста не пройдена:")
            for error in errors:
                print(f"  - {error}")
            raise SystemExit(1)

        print(
            f"Манифест проверен: "
            f"{len(manifest['files'])} CSV без расхождений"
        )


if __name__ == "__main__":
    main()