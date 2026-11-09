import argparse
import csv
import json
import sys
from pathlib import Path

import psycopg
from psycopg import sql


ROOT = Path(__file__).resolve().parents[1]
SETUP_DIR = ROOT / "sql" / "setup"
MANIFEST_PATH = ROOT / "data_manifest.json"

sys.path.insert(0, str(ROOT / "src"))

from data_manifest import CSV_SOURCES, verify_manifest


# CSV -> таблица, столбцы, поля для FORCE_NULL
CSV_TABLES = {
    "first_questions_2023.csv": (
        "first_questions_2023",
        ("user_id", "first_question_id", "first_question_at"),
        (),
    ),
    "answers_to_2023_questions.csv": (
        "answers_to_2023_questions",
        ("answer_id", "question_id", "answer_author_id", "answer_at"),
        ("answer_author_id",),
    ),
    "posts_activity_2023.csv": (
        "posts_activity_2023",
        ("post_id", "user_id", "post_type_id", "event_at"),
        (),
    ),
    "comments_2023_h1.csv": (
        "comments_activity",
        ("comment_id", "user_id", "post_id", "event_at"),
        (),
    ),
    "comments_2023_h2.csv": (
        "comments_activity",
        ("comment_id", "user_id", "post_id", "event_at"),
        (),
    ),
    "comments_2024_jan.csv": (
        "comments_activity",
        ("comment_id", "user_id", "post_id", "event_at"),
        (),
    ),
    "user_registration_2023.csv": (
        "user_registration_2023",
        ("user_id", "first_question_at", "account_created_at"),
        ("account_created_at",),
    ),
    "initial_question_metadata_2023.csv": (
        "initial_question_metadata_2023",
        (
            "question_id",
            "initial_title",
            "initial_tags",
            "title_events",
            "tag_events",
        ),
        ("initial_title", "initial_tags"),
    ),
}


def preflight() -> dict:
    """Проверить манифест и структуру CSV до подключения к БД."""

    manifest = json.loads(
        MANIFEST_PATH.read_text(encoding="utf-8")
    )

    errors = verify_manifest(ROOT, manifest)

    if errors:
        raise ValueError(
            "Проверка манифеста не пройдена:\n"
            + "\n".join(errors)
        )

    if set(CSV_TABLES) != set(CSV_SOURCES):
        raise ValueError(
            "Список CSV в загрузчике не совпадает с манифестом"
        )

    for filename, (_, columns, _) in CSV_TABLES.items():
        path = ROOT / "data" / "raw" / filename

        with path.open(
            "r", encoding="utf-8-sig", newline=""
        ) as file:
            header = next(csv.reader(file), None)

        if header != list(columns):
            raise ValueError(
                f"{filename}: неверные заголовки CSV.\n"
                f"Ожидается: {list(columns)}\n"
                f"Получено: {header}"
            )

    return manifest


def table_identifier(table: str):
    return sql.Identifier("raw", table)


def run_setup(cur, filenames):
    """Выполнить существующие SQL-файлы создания таблиц."""
    for filename in filenames:
        script = (SETUP_DIR / filename).read_text(
            encoding="utf-8"
        )
        cur.execute(script)


def make_copy_statement(table, columns, null_columns):
    """Сформировать безопасный COPY-запрос."""

    table_name = table_identifier(table)

    column_names = sql.SQL(", ").join(
        sql.Identifier(column) for column in columns
    )

    options = sql.SQL(
        "FORMAT CSV, HEADER TRUE, NULL ''"
    )

    if null_columns:
        options += sql.SQL(", FORCE_NULL ({})").format(
            sql.SQL(", ").join(
                sql.Identifier(column)
                for column in null_columns
            )
        )

    return sql.SQL(
        "COPY {} ({}) FROM STDIN WITH ({})"
    ).format(table_name, column_names, options)


def copy_csv(cur, filename, table, columns, null_columns):
    """Загрузить CSV через PostgreSQL COPY."""
    path = ROOT / "data" / "raw" / filename

    statement = make_copy_statement(
        table, columns, null_columns
    )

    with path.open("rb") as file:
        with cur.copy(statement) as copy:
            while chunk := file.read(1024 * 1024):
                copy.write(chunk)


def load_data(dsn: str, replace: bool, confirm_db: str | None):
    """Создать таблицы и атомарно загрузить все CSV."""

    manifest = preflight()

    expected_rows = {
        entry["filename"]: entry["rows"]
        for entry in manifest["files"]
    }

    tables = list(dict.fromkeys(
        item[0] for item in CSV_TABLES.values()
    ))

    expected_table_rows = {table: 0 for table in tables}

    for filename, (table, _, _) in CSV_TABLES.items():
        expected_table_rows[table] += expected_rows[filename]

    # Контекст соединения фиксирует транзакцию только
    # при успешном завершении всего блока.
    # При любой ошибке происходит ROLLBACK.
    with psycopg.connect(dsn) as conn:

        database_name = conn.info.dbname

        if database_name in {
            "postgres", "template0", "template1"
        }:
            raise ValueError(
                "Загрузка в системную базу запрещена"
            )

        if replace and confirm_db != database_name:
            raise ValueError(
                "Для --replace необходимо указать "
                f"--confirm-db {database_name}"
            )

        with conn.cursor() as cur:
            cur.execute("SET LOCAL lock_timeout = '10s'")

            # Сначала создаём схемы и таблицы.
            setup_files = [
                f"{number:02d}_{name}.sql"
                for number, name in [
                    (1, "create_schemas"),
                    (2, "create_first_questions"),
                    (3, "create_answers"),
                    (4, "create_posts_activity"),
                    (5, "create_comments_activity"),
                    (6, "create_user_registration"),
                    (7, "create_question_metadata"),
                ]
            ]

            run_setup(cur, setup_files)

            identifiers = sql.SQL(", ").join(
                table_identifier(table) for table in tables
            )

            # Блокируем конкурирующие изменения на время загрузки.
            cur.execute(
                sql.SQL(
                    "LOCK TABLE {} IN ACCESS EXCLUSIVE MODE"
                ).format(identifiers)
            )

            nonempty_tables = []

            for table in tables:
                cur.execute(
                    sql.SQL(
                        "SELECT EXISTS (SELECT 1 FROM {})"
                    ).format(table_identifier(table))
                )

                if cur.fetchone()[0]:
                    nonempty_tables.append(table)

            if nonempty_tables and not replace:
                raise ValueError(
                    "База уже содержит исходные данные: "
                    + ", ".join(nonempty_tables)
                    + ". Для полной замены используй --replace "
                    "и --confirm-db."
                )

            if replace:
                cur.execute(
                    sql.SQL("TRUNCATE TABLE {}").format(
                        identifiers
                    )
                )

            # Первичные ключи устанавливаются до COPY.
            run_setup(cur, ["08_add_primary_keys.sql"])

            for filename, specification in CSV_TABLES.items():
                table, columns, null_columns = specification

                copy_csv(
                    cur,
                    filename,
                    table,
                    columns,
                    null_columns,
                )

            # Проверка фактического количества строк.
            for table, expected in expected_table_rows.items():
                cur.execute(
                    sql.SQL("SELECT COUNT(*) FROM {}").format(
                        table_identifier(table)
                    )
                )

                actual = cur.fetchone()[0]

                if actual != expected:
                    raise ValueError(
                        f"raw.{table}: ожидалось {expected} "
                        f"строк, получено {actual}"
                    )

    # Сюда попадаем только после успешного COMMIT.
    print("Загрузка завершена успешно.")
    print(f"База: {database_name}")

    for table, count in expected_table_rows.items():
        print(f"  raw.{table}: {count} строк")


def main():
    parser = argparse.ArgumentParser(
        description="Атомарная загрузка CSV в PostgreSQL"
    )

    parser.add_argument(
        "--dsn",
        default="dbname=stackexchange_analytics",
        help="Строка подключения к PostgreSQL",
    )

    parser.add_argument(
        "--replace",
        action="store_true",
        help="Атомарно заменить существующие исходные данные",
    )

    parser.add_argument(
        "--confirm-db",
        help="Подтвердить имя БД для операции --replace",
    )

    args = parser.parse_args()

    try:
        load_data(args.dsn, args.replace, args.confirm_db)
    except (
        OSError,
        ValueError,
        RuntimeError,
        psycopg.Error,
    ) as error:
        parser.exit(
            1,
            f"Загрузка не выполнена: {error}\n"
        )


if __name__ == "__main__":
    main()