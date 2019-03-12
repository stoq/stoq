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
  return LOWER(public.unaccent(input_string));
END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION validate_stock_item() RETURNS trigger AS $$
DECLARE
    count_ int;
    errmsg text;
BEGIN
    -- Only allow updates that are not touching quantity/stock_cost
    IF (TG_OP = 'UPDATE' AND
        NEW.quantity = OLD.quantity AND
        NEW.stock_cost = OLD.stock_cost) THEN
        RETURN NEW;
    END IF;

    BEGIN
        SELECT COUNT(1) INTO count_ FROM __inserting_sth
            WHERE warning_note = (
                E'I SHOULD ONLY INSERT OR UPDATE DATA ON PRODUCT_STOCK_ITEM BY ' ||
                E'INSERTING A ROW ON STOCK_TRANSACTION_HISTORY, OTHERWISE MY ' ||
                E'DATABASE WILL BECOME INCONSISTENT. I\'M HEREBY WARNED');
    EXCEPTION WHEN undefined_table THEN
        count_ := 0;
    END;

    IF count_ = 0 THEN
        -- Postgresql will give us a syntaxerror if we try to break
        -- the string in the RAISE EXCEPTION statement
        errmsg := ('product_stock_item should not be inserted or have its ' ||
                   'quantity/stock_cost columns updated manually. ' ||
                   'To do that, insert a row on stock_transaction_history');
        RAISE EXCEPTION '%', errmsg;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
