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


% if db_version[0] >= 9:
  -- Postgres 9.0+

  -- Enable unaccent extension
  CREATE EXTENSION IF NOT EXISTS unaccent;

  CREATE OR REPLACE FUNCTION stoq_normalize_string(input_string text) RETURNS text AS $$
    BEGIN
      input_string := LOWER(input_string);
      return unaccent(input_string);
    END;
  $$ LANGUAGE plpgsql IMMUTABLE;

% else:
  -- Postgres 8.4

  --
  -- This is used to remove accents from a string
  --
  -- Source: http://wiki.postgresql.org/wiki/Strip_accents_from_strings,_and_output_in_lowercase
  -- Author: Thom Brown
  --
  -- Source: http://lehelk.com/2011/05/06/script-to-remove-diacritics/
  --

  CREATE OR REPLACE FUNCTION stoq_normalize_string(input_string text) RETURNS text AS $$
    BEGIN
      input_string := LOWER(input_string);

      -- These are the must common cases for latin based character sets,
      -- and based on code suggested by django:
      -- https://django-orm.readthedocs.org/en/latest/orm-pg-fulltext.html
      input_string := translate(input_string, 'àáâäãåāăą', 'aaaaaaaaa');
      input_string := translate(input_string, 'èéêëēĕėęě', 'eeeeeeeee');
      input_string := translate(input_string, 'ìíîïĩīĭ', 'iiiiiii');
      input_string := translate(input_string, 'òóôöõōŏő', 'oooooooo');
      input_string := translate(input_string, 'ùúûüũūŭů', 'uuuuuuuu');
      input_string := translate(input_string, 'ñç', 'nc');

      return input_string;
    END;
  $$ LANGUAGE plpgsql IMMUTABLE;

% endif
