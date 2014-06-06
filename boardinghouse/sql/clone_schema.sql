-- http://wiki.postgresql.org/wiki/Clone_schema

CREATE OR REPLACE FUNCTION clone_schema(source_schema text, dest_schema text) RETURNS void AS
$$

DECLARE
  object text;
  buffer text;
  default_ text;
  column_ text;
  trigger_ text;
BEGIN
  EXECUTE 'CREATE SCHEMA ' || dest_schema ;
  
  -- TODO: Find a way to make this sequence's owner is the correct column.
  -- Not a huge priority.
  FOR object IN
    SELECT 
      sequence_name::text
    FROM
      information_schema.SEQUENCES
    WHERE
      sequence_schema = source_schema
  LOOP
    EXECUTE 'CREATE SEQUENCE ' || dest_schema || '.' || object;
  END LOOP;
  
  -- Iterate through all tables in the source schema.
  FOR object IN
    SELECT
      table_name::text
    FROM
      information_schema.TABLES
    WHERE
      table_schema = source_schema
  LOOP
    -- Create a table with the relevant data in the new schema.
    buffer := dest_schema || '.' || object;
    EXECUTE 'CREATE TABLE ' || buffer || ' (LIKE ' || source_schema || '.' || object || ' INCLUDING CONSTRAINTS INCLUDING INDEXES INCLUDING DEFAULTS)';
    
    -- Ensure any default values that refer to the old schema now refer to the new schema.
    FOR column_, default_ IN
      SELECT
        column_name::text,
        replace(column_default::text, source_schema, dest_schema)
      FROM
        information_schema.COLUMNS
      WHERE
        table_schema = dest_schema
      AND
        table_name = object
      AND
        column_default LIKE 'nextval(%' || source_schema || '%::regclass)'
    LOOP
      EXECUTE 'ALTER TABLE ' || buffer || ' ALTER COLUMN ' || column_ || ' SET DEFAULT ' || default_;
    END LOOP;
    
    -- Ensure any triggers also come across...
    -- We can do the same trick we did for the default values.
    FOR trigger_ IN
      SELECT
        replace(pg_catalog.pg_get_triggerdef(oid, false)::text, source_schema, dest_schema)
      FROM pg_catalog.pg_trigger
      WHERE tgrelid = (source_schema || '.' || object)::regclass::pg_catalog.oid
      AND NOT tgisinternal
    LOOP
      EXECUTE trigger_;
    END LOOP;

  END LOOP;
 
END;

$$ LANGUAGE plpgsql VOLATILE;