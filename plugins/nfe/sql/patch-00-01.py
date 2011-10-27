# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

from kiwi.environ import environ

def apply_patch(trans):
    trans.query("""CREATE TABLE nfe_city_data (
                        id bigserial NOT NULL PRIMARY KEY,
                        state_code integer,
                        state_name text,
                        city_code integer,
                        city_name text);
    """)

    csv_file = environ.find_resource('nfecsv', 'dtb_brazilian_city_codes.csv')
    trans.query("""
        COPY nfe_city_data (state_code, state_name, city_code, city_name)
            FROM '%s' WITH CSV HEADER;
    """ % csv_file)
    trans.query("""CREATE INDEX nfe_city_name_state_code_idx  ON
                           nfe_city_data (city_name, state_code);""")
    trans.commit()
