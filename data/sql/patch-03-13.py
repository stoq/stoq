from stoqlib.domain.person import LoginUser


def apply_patch(store):
    store.execute("""
        ALTER TABLE login_user RENAME COLUMN password TO pw_hash;
          """)

    for user in LoginUser.select(store=store):
        user.set_password(user.pw_hash or '')
