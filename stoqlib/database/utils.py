def _select_rows_ids_in_batch(store, table_cls, column_name, limit):
    kwargs = {column_name: None}
    return list(
        store.find(table_cls, **kwargs).config(limit=limit).values(table_cls.id)
    )


def _update_rows_batch(store, table_cls, column_name, default, limit):
    col = getattr(table_cls, 'id')
    update_kwargs = {column_name: default}

    ids = _select_rows_ids_in_batch(store, table_cls, column_name, limit)
    while ids:
        store.find(table_cls, col.is_in(ids)).set(**update_kwargs)
        ids = _select_rows_ids_in_batch(store, table_cls, column_name, limit)


def add_default_to_column(
    store, table_cls, *, column_name, default, batch_update_count=1000
):
    """
    This function alters the column to set default values and update all the
    rows to this value without locking the table agressively in order to
    decrease the database downtime when running the migration.
    """

    table_name = table_cls.__storm_table__

    store.execute("""ALTER TABLE {} ALTER COLUMN {} SET DEFAULT {}""".format(
        table_name, column_name, default
    ))
    _update_rows_batch(store, table_cls, column_name, default, limit=batch_update_count)
    store.execute(
        "ALTER TABLE {} ALTER COLUMN {} SET NOT NULL".format(table_name, column_name)
    )
