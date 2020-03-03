DO $$
  BEGIN
    BEGIN
      ALTER TABLE address ADD COLUMN coordinates point;
    EXCEPTION
      WHEN duplicate_column THEN RAISE NOTICE 'Colunm `coordinates already exists`';
    END;
  End;
$$;
