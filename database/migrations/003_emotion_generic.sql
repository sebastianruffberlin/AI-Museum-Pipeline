-- ============================================================================
-- Migration: legacy Emotion result tables -> generic Emotion persistence
--
-- Museum-specific vocabulary/concept tables and views remain untouched.
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS museum;


DO $$
BEGIN
    IF to_regclass('museum.emotion') IS NOT NULL
       AND to_regclass('museum.emotion_assignments') IS NULL THEN
        ALTER TABLE museum.emotion
            RENAME TO emotion_assignments;
    END IF;

    IF to_regclass('museum.emotion_lauf') IS NOT NULL
       AND to_regclass('museum.emotion_runs') IS NULL THEN
        ALTER TABLE museum.emotion_lauf
            RENAME TO emotion_runs;
    END IF;
END
$$;


DO $$
DECLARE
    old_name text;
    new_name text;
BEGIN
    IF to_regclass('museum.emotion_runs') IS NOT NULL THEN
        FOR old_name, new_name IN
            SELECT *
            FROM (VALUES
                ('lesarten_count',            'reading_count'),
                ('befund_sichtbar',           'visible_findings'),
                ('situation_dargestellt',      'depicted_situations'),
                ('freie_wirkung',              'free_effects'),
                ('nicht_mappbar',              'unmappable_effects'),
                ('erwogen_verworfen',          'considered_rejected'),
                ('keine_lesart_begruendung',   'no_reading_reason')
            ) AS names(old_name, new_name)
        LOOP
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema='museum'
                  AND table_name='emotion_runs'
                  AND column_name=old_name
            )
            AND NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema='museum'
                  AND table_name='emotion_runs'
                  AND column_name=new_name
            ) THEN
                EXECUTE format(
                    'ALTER TABLE museum.emotion_runs RENAME COLUMN %I TO %I',
                    old_name,
                    new_name
                );
            END IF;
        END LOOP;
    END IF;
END
$$;


-- Provenance must come from the profile/runtime, not reference-schema defaults.
DO $$
BEGIN
    IF to_regclass('museum.emotion_assignments') IS NOT NULL THEN
        ALTER TABLE museum.emotion_assignments
            ALTER COLUMN perspective_type DROP DEFAULT,
            ALTER COLUMN vocabulary_version DROP DEFAULT;
    END IF;

    IF to_regclass('museum.emotion_runs') IS NOT NULL THEN
        ALTER TABLE museum.emotion_runs
            ALTER COLUMN vocabulary_version DROP DEFAULT;
    END IF;
END
$$;


-- Preserve identity sequences, but give them canonical names.
DO $$
BEGIN
    IF to_regclass('museum.emotion_id_seq') IS NOT NULL
       AND to_regclass('museum.emotion_assignments_id_seq') IS NULL THEN
        ALTER SEQUENCE museum.emotion_id_seq
            RENAME TO emotion_assignments_id_seq;
    END IF;

    IF to_regclass('museum.emotion_lauf_id_seq') IS NOT NULL
       AND to_regclass('museum.emotion_runs_id_seq') IS NULL THEN
        ALTER SEQUENCE museum.emotion_lauf_id_seq
            RENAME TO emotion_runs_id_seq;
    END IF;
END
$$;
