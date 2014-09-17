--
-- Copyright (C) 2012 Async Open Source
--
-- This program is free software; you can redistribute it and/or
-- modify it under the terms of the GNU Lesser General Public License
-- as published by the Free Software Foundation; either version 2
-- of the License, or (at your option) any later version.
--
-- This program is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- GNU Lesser General Public License for more details.
--
-- You should have received a copy of the GNU Lesser General Public License
-- along with this program; if not, write to the Free Software
-- Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
--
--
-- Author(s): Stoq Team <stoq-devel@async.com.br>
--

--
-- Stoq SQL function library
--

<%!
  from stoqlib.database.settings import get_database_version, db_settings

  store = db_settings.create_store()
  db_version = get_database_version(store)
  store.close()
%>

--
-- Source: http://wiki.postgresql.org/wiki/CREATE_OR_REPLACE_LANGUAGE
-- Author: David Fetter
--

CREATE OR REPLACE FUNCTION stoq_create_language_plpgsql()
RETURNS VOID
LANGUAGE SQL
AS $$
CREATE LANGUAGE plpgsql;
$$;

SELECT
    CASE
    WHEN EXISTS(
        SELECT 1
        FROM pg_catalog.pg_language
        WHERE lanname = 'plpgsql'
    )
    THEN NULL
    ELSE stoq_create_language_plpgsql() END;

DROP FUNCTION stoq_create_language_plpgsql();

-- Enable unaccent extension
CREATE EXTENSION IF NOT EXISTS unaccent;

CREATE OR REPLACE FUNCTION stoq_normalize_string(input_string text) RETURNS text AS $$
BEGIN
  input_string := LOWER(input_string);
  return unaccent(input_string);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Returns a default te_id for the domain tables
CREATE OR REPLACE FUNCTION new_te() RETURNS integer AS $$
    DECLARE te_id integer;
BEGIN
    INSERT INTO transaction_entry (te_time, dirty) VALUES (STATEMENT_TIMESTAMP(), true) RETURNING id INTO te_id;
    RETURN te_id;
END;
$$ LANGUAGE plpgsql;

-- Updates the transaction entry for the given id
CREATE OR REPLACE FUNCTION update_te(te_id bigint) RETURNS void AS $$
BEGIN
    UPDATE transaction_entry SET te_time = STATEMENT_TIMESTAMP(), dirty = true WHERE id = $1;
END;
$$ LANGUAGE plpgsql;
