-- ============================================================================
-- Migration: legacy Schwerpunkt result tables -> generic Topics result tables
--
-- Preserves existing data. Museum-specific taxonomy/resource tables such as
-- schwerpunkt_wissen and schwerpunkt_unterthema are intentionally untouched.
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS museum;

DO $$
BEGIN
    IF to_regclass('museum.schwerpunkt_bezug') IS NOT NULL
       AND to_regclass('museum.topic_assignments') IS NULL THEN
        ALTER TABLE museum.schwerpunkt_bezug
            RENAME TO topic_assignments;
    END IF;

    IF to_regclass('museum.schwerpunkt_lauf') IS NOT NULL
       AND to_regclass('museum.topic_runs') IS NULL THEN
        ALTER TABLE museum.schwerpunkt_lauf
            RENAME TO topic_runs;
    END IF;
END
$$;


DO $$
DECLARE
    old_name text;
    new_name text;
BEGIN
    IF to_regclass('museum.topic_assignments') IS NOT NULL THEN
        FOR old_name, new_name IN
            SELECT *
            FROM (VALUES
                ('schwerpunkt',        'topic'),
                ('quelle',             'source'),
                ('bezugstyp',          'relation_types'),
                ('begruendung',        'rationale'),
                ('judge_entscheidung', 'judge_decision'),
                ('pruefklasse',        'review_class'),
                ('pflichtpruefung',    'mandatory_review'),
                ('taxonomie_version',  'taxonomy_version')
            ) AS names(old_name, new_name)
        LOOP
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'museum'
                  AND table_name = 'topic_assignments'
                  AND column_name = old_name
            )
            AND NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'museum'
                  AND table_name = 'topic_assignments'
                  AND column_name = new_name
            ) THEN
                EXECUTE format(
                    'ALTER TABLE museum.topic_assignments RENAME COLUMN %I TO %I',
                    old_name,
                    new_name
                );
            END IF;
        END LOOP;
    END IF;
END
$$;


DO $$
DECLARE
    old_name text;
    new_name text;
BEGIN
    IF to_regclass('museum.topic_runs') IS NOT NULL THEN
        FOR old_name, new_name IN
            SELECT *
            FROM (VALUES
                ('objektbefund',       'object_findings'),
                ('taxonomie_version',  'taxonomy_version'),
                ('n_bezuege',          'assignment_count'),
                ('erstellt_am',        'created_at')
            ) AS names(old_name, new_name)
        LOOP
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'museum'
                  AND table_name = 'topic_runs'
                  AND column_name = old_name
            )
            AND NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'museum'
                  AND table_name = 'topic_runs'
                  AND column_name = new_name
            ) THEN
                EXECUTE format(
                    'ALTER TABLE museum.topic_runs RENAME COLUMN %I TO %I',
                    old_name,
                    new_name
                );
            END IF;
        END LOOP;
    END IF;
END
$$;


-- Remove Stadtmuseum/model-profile defaults inherited from the legacy schema.
DO $$
BEGIN
    IF to_regclass('museum.topic_assignments') IS NOT NULL THEN
        ALTER TABLE museum.topic_assignments
            ALTER COLUMN taxonomy_version DROP DEFAULT;
    END IF;

    IF to_regclass('museum.topic_runs') IS NOT NULL THEN
        ALTER TABLE museum.topic_runs
            ALTER COLUMN generator_model DROP DEFAULT,
            ALTER COLUMN judge_model DROP DEFAULT;
    END IF;
END
$$;


-- Rename the legacy bigserial sequence when present.
DO $$
BEGIN
    IF to_regclass('museum.schwerpunkt_bezug_id_seq') IS NOT NULL
       AND to_regclass('museum.topic_assignments_id_seq') IS NULL THEN
        ALTER SEQUENCE museum.schwerpunkt_bezug_id_seq
            RENAME TO topic_assignments_id_seq;
    END IF;
END
$$;
