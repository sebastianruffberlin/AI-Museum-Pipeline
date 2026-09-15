from pathlib import Path


def test_force_cleanup_text_embedding_like_is_parameterized():
    """
    Regression guard for the Test-B --force failure.

    psycopg interprets percent signs in query strings as placeholder syntax.
    A literal LIKE 'text_%' therefore caused:

        ProgrammingError:
        only '%s', '%b', '%t' are allowed as placeholders, got '%''

    The LIKE pattern must be passed as a query parameter.
    """
    src = Path(
        "src/museum_pipeline/persistence/postgres.py"
    ).read_text()

    assert "kind LIKE 'text_%'" not in src
    assert "kind LIKE %s" in src

    assert (
        '(obj_id, "text_%")' in src
        or "(obj_id, 'text_%')" in src
    )
