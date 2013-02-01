# -*- coding: utf-8 -*-

from storm.expr import And, Lower

from stoqlib.database.expr import StoqNormalizeString
from stoqlib.database.orm import ORMObject
from stoqlib.database.properties import UnicodeCol, IntCol


class CityLocation(ORMObject):
    __storm_table__ = 'city_location'
    id = IntCol(primary=True)
    country = UnicodeCol(default=u"")
    city = UnicodeCol(default=u"")
    state = UnicodeCol(default=u"")
    city_code = IntCol(default=None)
    state_code = IntCol(default=None)


# This was used on last patch to mark new cities and to avoid
# problems with unique constraint
_COUNTRY_MARKER = u'__BRA__'


def apply_patch(store):
    cities = store.find(CityLocation,
                        CityLocation.country != _COUNTRY_MARKER)
    for city_location in cities:
        clause = And(
            Lower(CityLocation.state) == city_location.state.lower(),
            (StoqNormalizeString(CityLocation.city) ==
             StoqNormalizeString(city_location.city)))
        alikes = list(store.find(CityLocation, clause))
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
            store.execute("""
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
    store.execute("""
        UPDATE city_location
            SET country = '%s' WHERE country = '%s';
        """ % (u'Brazil', _COUNTRY_MARKER))

    # Also, do s/Brasil/Brazil/ for city_locations registered that way,
    # maybe because of birth location that had country as a textfield.
    # It's safe to do this since we did the normalization above
    # not taking country in consideration.
    store.execute("""
        UPDATE city_location
            SET country = 'Brazil' WHERE lower(country) = 'brasil';
        """)

    # Since COUNTRY_SUGGESTED was a free field, try to correct it if
    # some user changed it to Brasil (with 's' instead of 'z').
    store.execute("""
        UPDATE parameter_data
            SET field_value = 'Brazil'
            WHERE lower(field_value) = 'brasil' AND field_name = 'COUNTRY_SUGGESTED';
        """)
