import csv

import pkg_resources

from stoqlib.database.properties import UnicodeCol
from stoqlib.migration.domainv4 import Domain

_ncm_cest_map = None


def get_ncm_cest_map():
    """Returns a dictionary that maps an NCM to its corresponding CEST(s)

    This function will loop trough `data/csv/cest/ncm_cest_map.csv` and build a
    dictionary that maps a NCM to its corresponding CEST(s), returning a
    structure like:

    {
        `<ncm>`: [
            `<cest>`
            [... other possible CESTs]
        ],
        [... other NCMs]
    }

    :returns: A dictionary mapping a given NCM to its corresponding CEST(s)
    """
    global _ncm_cest_map

    if _ncm_cest_map is not None:
        # CEST table already loaded, just return it.
        return _ncm_cest_map

    # CEST table not loaded, load it and return it
    #
    # CEST table come in a format like:
    #
    # <cest>,<ncm>
    #
    # But some rows may contain only:
    #
    # <nothing>,<ncm>
    #
    # This means the NCM is related to the CEST that is listed above it, so
    # we'll need to always know what was the last seen CEST
    _ncm_cest_map = {}
    filename = pkg_resources.resource_filename('stoq', 'csv/cest/ncm_cest_map.csv')
    with open(filename) as csvfile:
        last_filled_row = None
        for row in csv.reader(csvfile):
            # Unpack the fields we are interested in
            cest, ncm = row[:2]

            if not ncm.isdigit():
                # Some rows may be headers or empty, on these cases, we check
                # to see if the NCM is actually an integer - if it is not, we
                # ignore it
                continue

            if cest:
                # If it has a CEST, this means it is a common row, with
                # everything we would expect in it.
                last_filled_row = row
            else:
                # If it does not have a CEST, we'll use the last filled row for
                # the CEST, the NCM remains the same.
                cest, _ = last_filled_row[:2]

            # Add the CEST and the NCM key
            _ncm_cest_map.setdefault(ncm, [])
            _ncm_cest_map[ncm].append(str(cest))
    return _ncm_cest_map


def get_cest_from_ncm(ncm):
    """Returns the CEST(s) related to a given NCM"""
    # Just making sure ncm will be a string
    ncm = str(ncm)
    ncm_cest_map = get_ncm_cest_map()
    for length in range(len(ncm), 0, -1):
        # Example:
        #
        # Try to find CESTs for NCM 22011456
        # Try to find CESTs for NCM 2201145
        # Try to find CESTs for NCM 220114
        # Try to find CESTs for NCM 22011
        # ...
        value = ncm_cest_map.get(ncm[:length])
        if value is not None:
            return value
    return None


class Product(Domain):
    __storm_table__ = 'product'

    cest = UnicodeCol()
    ncm = UnicodeCol()


def apply_patch(store):
    # Add CEST column
    store.execute("ALTER TABLE product ADD COLUMN cest TEXT;")

    # Then try to match the NCM with the corresponding CEST
    for product in store.find(Product):
        cest_data = get_cest_from_ncm(product.ncm)
        # Do not attempt to set the CEST for products that have more than one
        # available CEST or products that have no mapped CEST. We'll let the
        # user deal with his options later.
        if cest_data is not None and len(cest_data) == 1:
            product.cest = cest_data[0]
