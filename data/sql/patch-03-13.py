from stoqlib.domain.person import LoginUser


def apply_patch(trans):
    trans.query("""
        ALTER TABLE login_user RENAME COLUMN password TO pw_hash;
          """)

    for user in LoginUser.select(connection=trans):
        user.set_password(user.pw_hash or '')
