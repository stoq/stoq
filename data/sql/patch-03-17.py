# -*- coding: utf-8 -*-

from stoqlib.database.orm import func, AND
from stoqlib.domain.address import CityLocation


# This was used on last patch to mark new cities and to avoid
# problems with unique constraint
_COUNTRY_MARKER = '__BRA__'


def apply_patch(trans):
    for city_location in CityLocation.select(clause=(CityLocation.q.country !=
                                                     _COUNTRY_MARKER),
                                             connection=trans):
        clause = AND(
            func.LOWER(CityLocation.q.state) == city_location.state.lower(),
            (func.stoq_normalize_string(CityLocation.q.city) ==
             func.stoq_normalize_string(city_location.city)))
        alikes = list(CityLocation.select(clause=clause,
                                          connection=trans))
        if len(alikes) > 1:
            for location in alikes:
                if location.country == _COUNTRY_MARKER:
                    # This is a new city location we just added on
                    # the last patch. Use it for right_location
                    right_location = location
                    break
            else:
                right_location = alikes[0]

            in_str = ', '.join([str(cl.id) for cl in alikes if
                                cl != right_location])
            # Make all alikes point to right_location and remove them
            trans.query("""
                UPDATE address
                    SET city_location_id = %(right_location_id)d
                    WHERE city_location_id IN (%(in_str)s);
                UPDATE individual
                    SET birth_location_id = %(right_location_id)d
                    WHERE birth_location_id IN (%(in_str)s);
                DELETE FROM city_location WHERE id IN (%(in_str)s);
                """ % dict(right_location_id=right_location.id,
                           in_str=in_str))

    # Now it's safe to return __BRA__ to Brazil
    trans.query("""
        UPDATE city_location
            SET country = '%s' WHERE country = '%s';
        """ % ('Brazil', _COUNTRY_MARKER))

    # Also, do s/Brasil/Brazil/ for city_locations registered that way,
    # maybe because of birth location that had country as a textfield.
    # It's safe to do this since we did the normalization above
    # not taking country in consideration.
    trans.query("""
        UPDATE city_location
            SET country = 'Brazil' WHERE lower(country) = 'brasil';
        """)

    # Since COUNTRY_SUGGESTED was a free field, try to correct it if
    # some user changed it to Brasil (with 's' instead of 'z').
    trans.query("""
        UPDATE parameter_data
            SET field_value = 'Brazil'
            WHERE lower(field_value) = 'brasil' AND field_name = 'COUNTRY_SUGGESTED';
        """)
