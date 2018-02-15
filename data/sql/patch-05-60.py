def apply_patch(store):
    # This patch might be applied by a plugin before the release. So we must
    # check if the column already exists before.
    rows = store.execute(
        "SELECT COUNT(column_name) FROM information_schema.columns WHERE "
        "table_name='individual' and column_name = 'state_registry'")
    if rows.get_one()[0]:
        return

    store.execute("ALTER TABLE individual "
                  "ADD COLUMN state_registry TEXT, "
                  "ADD COLUMN city_registry TEXT;")
