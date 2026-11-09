from datetime import datetime, timedelta
import os
from pathlib import Path

import psycopg
import pytest


ROOT = Path(__file__).resolve().parents[1]
SETUP_DIR = ROOT / "sql" / "setup"
RETENTION_VIEW_SQL = (
    ROOT / "sql" / "marts" / "07_return_outside_first_thread_2023.sql"
)

USER_ID = 101
FIRST_QUESTION_ID = 1001
FIRST_QUESTION_AT = datetime(2023, 6, 1, 12, 0, 0)


def at(*, days=0, hours=0, seconds=0):
    return FIRST_QUESTION_AT + timedelta(
        days=days, hours=hours, seconds=seconds
    )


@pytest.fixture
def pg_conn():
    """Create production-shaped tables in a transaction that is rolled back."""
    dsn = os.environ.get("TEST_DATABASE_URL")
    if not dsn:
        pytest.skip("Set TEST_DATABASE_URL to run PostgreSQL integration tests")

    conn = psycopg.connect(dsn)
    try:
        if conn.info.dbname != "stackexchange_retention_test":
            pytest.fail(
                "Integration tests must use the dedicated "
                "stackexchange_retention_test database, not an analytics database"
            )

        with conn.cursor() as cur:
            cur.execute("CREATE SCHEMA raw")
            cur.execute("CREATE SCHEMA analytics")
            for filename in (
                "02_create_first_questions.sql",
                "03_create_answers.sql",
                "04_create_posts_activity.sql",
                "05_create_comments_activity.sql",
            ):
                cur.execute((SETUP_DIR / filename).read_text(encoding="utf-8"))

        yield conn
    finally:
        # In particular, never commit the synthetic rows to PostgreSQL.
        conn.rollback()
        conn.close()


@pytest.mark.parametrize(
    "posts, comments, answers, expected",
    [
        pytest.param(
            [],
            [(5001, USER_ID, FIRST_QUESTION_ID, at(days=3))],
            [],
            (0, 0, False),
            id="comment-on-first-question-is-excluded",
        ),
        pytest.param(
            [],
            [(5002, USER_ID, 2001, at(days=3))],
            [(2001, FIRST_QUESTION_ID, 777, at(hours=2))],
            (0, 0, False),
            id="comment-on-first-answer-is-excluded",
        ),
        pytest.param(
            [(3001, USER_ID, 1, at(days=3))],
            [],
            [],
            (1, 0, True),
            id="second-question-is-return",
        ),
        pytest.param(
            [(3002, USER_ID, 2, at(days=3))],
            [],
            [(3002, 9001, USER_ID, at(days=3))],
            (1, 0, True),
            id="answer-to-other-question-is-return",
        ),
        pytest.param(
            [(2003, USER_ID, 2, at(days=3))],
            [],
            [(2003, FIRST_QUESTION_ID, USER_ID, at(days=3))],
            (0, 0, False),
            id="answer-to-own-first-question-is-excluded",
        ),
        pytest.param(
            [(3010, USER_ID, 1, at(hours=6))],
            [(5009, USER_ID, 9999, at(hours=23))],
            [],
            (0, 0, False),
            id="activity-before-24-hours-is-excluded",
        ),
        pytest.param(
            [(3012, USER_ID, 1, at(days=1))],
            [],
            [],
            (0, 0, False),
            id="activity-exactly-at-24-hours-is-excluded",
        ),
        pytest.param(
            [(3013, USER_ID, 1, at(days=1, seconds=1))],
            [],
            [],
            (1, 0, True),
            id="activity-one-second-after-24-hours-is-return",
        ),
        pytest.param(
            [],
            [(5010, USER_ID, 9999, at(days=30))],
            [],
            (0, 1, True),
            id="activity-exactly-at-30-days-is-return",
        ),
        pytest.param(
            [(3014, USER_ID, 1, at(days=30, seconds=1))],
            [],
            [],
            (0, 0, False),
            id="activity-after-30-days-is-excluded",
        ),
        pytest.param(
            [],
            [(5011, USER_ID, 8888, at(days=3))],
            [],
            (0, 1, True),
            id="comment-on-other-thread-is-return",
        ),
        pytest.param(
            [
                (3015, USER_ID, 1, at(days=3)),
                (3016, USER_ID, 2, at(days=4)),
            ],
            [
                (5012, USER_ID, FIRST_QUESTION_ID, at(days=3)),
                (5013, USER_ID, 9002, at(days=4)),
                (5014, USER_ID, 9003, at(days=5)),
            ],
            [],
            (2, 2, True),
            id="multiple-events-are-counted-but-user-returns-once",
        ),
        pytest.param(
            [],
            [],
            [],
            (0, 0, False),
            id="no-activity-is-not-return",
        ),
    ],
)
def test_outside_first_thread_retention(
    pg_conn, posts, comments, answers, expected
):
    """Execute the *original* production view against independent events."""
    with pg_conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO raw.first_questions_2023
                (user_id, first_question_id, first_question_at)
            VALUES (%s, %s, %s)
            """,
            (USER_ID, FIRST_QUESTION_ID, FIRST_QUESTION_AT),
        )

        if answers:
            cur.executemany(
                """
                INSERT INTO raw.answers_to_2023_questions
                    (answer_id, question_id, answer_author_id, answer_at)
                VALUES (%s, %s, %s, %s)
                """,
                answers,
            )

        if posts:
            cur.executemany(
                """
                INSERT INTO raw.posts_activity_2023
                    (post_id, user_id, post_type_id, event_at)
                VALUES (%s, %s, %s, %s)
                """,
                posts,
            )

        if comments:
            cur.executemany(
                """
                INSERT INTO raw.comments_activity
                    (comment_id, user_id, post_id, event_at)
                VALUES (%s, %s, %s, %s)
                """,
                comments,
            )

        # Do not duplicate or reimplement the business logic in the test.
        cur.execute(RETENTION_VIEW_SQL.read_text(encoding="utf-8"))
        cur.execute(
            """
            SELECT other_posts_30d,
                   other_comments_30d,
                   returned_outside_first_thread_30d
            FROM analytics.return_outside_first_thread_2023
            WHERE user_id = %s
            """,
            (USER_ID,),
        )
        actual = cur.fetchone()

    assert actual == expected
