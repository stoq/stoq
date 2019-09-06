from stoqlib.database.utils import add_default_to_column
from stoqlib.domain.sellable import Sellable
from stoqlib.domain.station import BranchStation


def apply_patch(store):
    add_default_to_column(
        store,
        BranchStation,
        column_name='has_kps_enabled',
        default=False,
    )
    add_default_to_column(
        store,
        Sellable,
        column_name='requires_kitchen_production',
        default=False,
    )
