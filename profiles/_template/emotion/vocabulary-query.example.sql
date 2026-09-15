-- Example adapter for a museum-specific emotion vocabulary database.
-- The internal table design is up to the museum. The pipeline contract is only:
-- return exactly one row with a column named `value` containing a JSON array.
-- Each active runtime concept needs at least:
--   concept_id, begriff, definition
-- and should provide:
--   nicht_verwenden_wenn

SELECT jsonb_agg(
  jsonb_strip_nulls(
    jsonb_build_object(
      'concept_id', concept_id,
      'begriff', preferred_label,
      'definition', definition,
      'nicht_verwenden_wenn', to_jsonb(NULLIF(do_not_use_when, '{}'::text[]))
    )
  )
  ORDER BY preferred_label
)::text AS value
FROM my_schema.my_emotion_vocabulary
WHERE active = true;
