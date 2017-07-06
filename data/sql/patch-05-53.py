def apply_patch(store):
    # This patch could have been applied before it's official release, so we
    # must check if the columns is already present on the database.
    res = store.execute(
        "SELECT COUNT(column_name) FROM information_schema.columns WHERE "
        "table_name = 'delivery' AND column_name = 'volumes_net_weight'")
    if res.get_one()[0]:
        return

    store.execute("ALTER TABLE delivery "
                  "ADD COLUMN volumes_net_weight NUMERIC(10, 3), "
                  "ADD COLUMN volumes_gross_weight NUMERIC(10, 3), "
                  "ADD COLUMN vehicle_license_plate TEXT, "
                  "ADD COLUMN vehicle_state TEXT, "
                  "ADD COLUMN vehicle_registration TEXT;")
