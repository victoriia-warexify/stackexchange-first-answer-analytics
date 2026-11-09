import json
import os
import uuid

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from scripts import load_data as loader
from src.data_manifest import build_manifest, CSV_SOURCES


@pytest.fixture
def sample_files(tmp_path, monkeypatch):
    """Создать искусственные CSV и корректный манифест."""
    raw = tmp_path / "data" / "raw"
    raw.mkdir(parents=True)

    contents = {
        "first_questions_2023.csv": (
            "user_id,first_question_id,first_question_at\n"
            "101,1001,2023-06-01 12:00:00\n"
        ),
        "answers_to_2023_questions.csv": (
            "answer_id,question_id,answer_author_id,answer_at\n"
            '2001,1001,"",2023-06-02 12:00:00\n'
        ),
        "posts_activity_2023.csv": (
            "post_id,user_id,post_type_id,event_at\n"
            "1001,101,1,2023-06-01 12:00:00\n"
        ),
        "comments_2023_h1.csv": (
            "comment_id,user_id,post_id,event_at\n"
            "3001,101,1001,2023-06-02 12:00:00\n"
        ),
        "comments_2023_h2.csv": (
            "comment_id,user_id,post_id,event_at\n"
            "3002,101,1001,2023-08-02 12:00:00\n"
        ),
        "comments_2024_jan.csv": (
            "comment_id,user_id,post_id,event_at\n"
            "3003,101,1001,2024-01-02 12:00:00\n"
        ),
        "user_registration_2023.csv": (
            "user_id,first_question_at,account_created_at\n"
            "101,2023-06-01 12:00:00,2023-05-01 12:00:00\n"
        ),
        "initial_question_metadata_2023.csv": (
            "question_id,initial_title,initial_tags,"
            "title_events,tag_events\n"
            '1001,"",<regression>,1,1\n'
        ),
    }

    assert set(contents) == set(CSV_SOURCES)

    for filename, content in contents.items():
        (raw / filename).write_text(
            content, encoding="utf-8"
        )

    monkeypatch.setattr(loader, "ROOT", tmp_path)
    monkeypatch.setattr(
        loader, "MANIFEST_PATH",
        tmp_path / "data_manifest.json",
    )

    refresh_manifest(tmp_path)
    return tmp_path


def refresh_manifest(root):
    """Обновить манифест для тестовой выборки."""
    manifest = build_manifest(root)

    (root / "data_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False),
        encoding="utf-8",
    )


@pytest.fixture
def isolated_db():
    """Создать уникальную временную БД и удалить после теста."""
    dsn = os.environ.get("TEST_DATABASE_URL")

    if not dsn:
        pytest.skip("Не задан TEST_DATABASE_URL")

    if conninfo_to_dict(dsn).get("dbname") != (
        "stackexchange_retention_test"
    ):
        pytest.fail(
            "Тесты загрузчика требуют "
            "stackexchange_retention_test"
        )

    name = "stackexchange_loader_it_" + uuid.uuid4().hex[:12]
    admin_dsn = make_conninfo(dsn, dbname="postgres")
    test_dsn = make_conninfo(dsn, dbname=name)

    with psycopg.connect(
        admin_dsn, autocommit=True
    ) as admin:
        admin.execute(
            sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier(name)
            )
        )

    try:
        yield test_dsn, name
    finally:
        with psycopg.connect(
            admin_dsn, autocommit=True
        ) as admin:
            admin.execute(
                sql.SQL(
                    "DROP DATABASE {} WITH (FORCE)"
                ).format(sql.Identifier(name))
            )


def count_rows(dsn, table):
    with psycopg.connect(dsn) as conn:
        return conn.execute(
            sql.SQL("SELECT COUNT(*) FROM raw.{}").format(
                sql.Identifier(table)
            )
        ).fetchone()[0]


def corrupt_last_csv(root):
    """Добавить дубликат PK в последний CSV."""
    path = (
        root / "data/raw/"
        "initial_question_metadata_2023.csv"
    )

    with path.open("a", encoding="utf-8") as file:
        file.write(
            "1001,Duplicate,<regression>,1,1\n"
        )

    # Манифест обновляется намеренно:
    # проверяем ошибку PostgreSQL, а не ошибку SHA-256.
    refresh_manifest(root)


def test_successful_load(sample_files, isolated_db):
    dsn, _ = isolated_db

    loader.load_data(dsn, replace=False, confirm_db=None)

    assert count_rows(
        dsn, "first_questions_2023"
    ) == 1
    assert count_rows(
        dsn, "comments_activity"
    ) == 3

    # Проверка FORCE_NULL для quoted empty string.
    with psycopg.connect(dsn) as conn:
        author = conn.execute(
            "SELECT answer_author_id "
            "FROM raw.answers_to_2023_questions"
        ).fetchone()[0]

        title = conn.execute(
            "SELECT initial_title "
            "FROM raw.initial_question_metadata_2023"
        ).fetchone()[0]

    assert author is None
    assert title is None


def test_duplicate_load_is_rejected(
    sample_files, isolated_db
):
    dsn, _ = isolated_db

    loader.load_data(dsn, replace=False, confirm_db=None)

    with pytest.raises(
        ValueError, match="уже содержит исходные данные"
    ):
        loader.load_data(
            dsn, replace=False, confirm_db=None
        )

    assert count_rows(
        dsn, "first_questions_2023"
    ) == 1


def test_failed_load_rolls_back(
    sample_files, isolated_db
):
    dsn, _ = isolated_db
    corrupt_last_csv(sample_files)

    with pytest.raises(psycopg.errors.UniqueViolation):
        loader.load_data(
            dsn, replace=False, confirm_db=None
        )

    # Даже первая таблица не должна остаться созданной.
    with psycopg.connect(dsn) as conn:
        table = conn.execute(
            "SELECT to_regclass('raw.first_questions_2023')"
        ).fetchone()[0]

    assert table is None


def test_failed_replace_preserves_original_data(
    sample_files, isolated_db
):
    dsn, name = isolated_db

    loader.load_data(dsn, replace=False, confirm_db=None)

    corrupt_last_csv(sample_files)

    with pytest.raises(psycopg.errors.UniqueViolation):
        loader.load_data(
            dsn, replace=True, confirm_db=name
        )

    # Неудачный TRUNCATE + COPY должен быть отменён.
    assert count_rows(
        dsn, "first_questions_2023"
    ) == 1
    assert count_rows(
        dsn, "initial_question_metadata_2023"
    ) == 1