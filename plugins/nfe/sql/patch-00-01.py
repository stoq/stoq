# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

from kiwi.environ import environ

from nfedomain import NFeCityData
from utils import remove_accentuation

def apply_patch(trans):
    trans.query("""CREATE TABLE nfe_city_data (
                        id bigserial NOT NULL PRIMARY KEY,
                        te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
                        te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),

                        state_code integer,
                        state_name text,
                        city_code integer,
                        city_name text);
    """)

    csv = environ.find_resource('nfecsv', 'dtb_brazilian_city_codes.csv')
    for line in open(csv, 'r').readlines():
        state_code, state_name, city_code, city_name = line.split(',')
        # the first line contain the titles, lets ignore it.
        if state_code == '"UF"':
            continue

        # in *_name attributes we remove the extra spaces and the '"'
        # character.
        state_name = unicode(state_name.strip().strip('"'))
        city_name = unicode(city_name.strip().strip('"'))
        NFeCityData(state_code=int(state_code.strip('"')),
                    state_name=remove_accentuation(state_name),
                    city_code=int(city_code.strip('"')),
                    city_name=remove_accentuation(city_name),
                    connection=trans)
    trans.query("""CREATE INDEX nfe_city_name_state_code_idx  ON
                           nfe_city_data (city_name, state_code);""")
    trans.commit()
