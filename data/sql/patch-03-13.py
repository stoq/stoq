from stoqlib.database.properties import UnicodeCol
from stoqlib.migration.domainv1 import Domain
import hashlib


class LoginUser(Domain):
    __storm_table__ = 'login_user'
    pw_hash = UnicodeCol()

    def set_password(self, password):
        self.pw_hash = hashlib.md5((password or '').encode()).hexdigest()


def apply_patch(store):
    store.execute("""
        ALTER TABLE login_user RENAME COLUMN password TO pw_hash;
          """)

    for user in store.find(LoginUser):
        user.set_password(user.pw_hash or u'')
