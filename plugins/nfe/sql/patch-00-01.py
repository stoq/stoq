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

                        uf_code integer,
                        uf_name text,
                        city_code integer,
                        city_name text);
    """)

    csv = environ.find_resource('nfecsv', 'dtb_brazillian_city_codes.csv')
    for line in open(csv, 'r').readlines():
        uf, uf_name, city_code, city_name = line.split(',')
        # the first line contain the titles, lets ignore it.
        if uf == '"UF"':
            continue

        # in *_name attributes we remove the extra spaces and the '"'
        # character.
        uf_name = unicode(uf_name.strip().strip('"'))
        city_name = unicode(city_name.strip().strip('"'))
        NFeCityData(uf_code=int(uf.strip('"')),
                    uf_name=remove_accentuation(uf_name),
                    city_code=int(city_code.strip('"')),
                    city_name=remove_accentuation(city_name),
                    connection=trans)
    trans.commit()
