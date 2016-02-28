-- Trigger function that will, at the database level, prevent
-- anyone changing the boardinghouse_schema.schema value for
-- a saved schema.

CREATE FUNCTION reject_schema_column_change() RETURNS TRIGGER AS $$
  BEGIN
    RAISE EXCEPTION 'Schema cannot be renamed' USING HINT = OLD.schema;
  END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
  IF NOT EXISTS(
    SELECT * FROM "information_schema"."triggers"
    WHERE "event_object_table" = '{schema_model}'
    AND "trigger_name" = 'protect_boardinghouse_schema_column'
  ) AND EXISTS(
    SELECT * FROM "information_schema".tables
    WHERE "table_name" = '{schema_model}'
    AND "table_schema" = '{public_schema}'
  ) THEN
    CREATE TRIGGER "protect_boardinghouse_schema_column"
      BEFORE UPDATE OF "schema" ON "{public_schema}"."{schema_model}"
      FOR EACH ROW
      WHEN (OLD."schema" IS DISTINCT FROM NEW."schema")
      EXECUTE PROCEDURE reject_schema_column_change();
  END IF;
END;
$$
