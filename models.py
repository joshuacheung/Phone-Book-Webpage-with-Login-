"""
This file defines the database models
"""
import datetime

from . common import db, Field, auth
from pydal.validators import *

### Define your table below
#
# db.define_table('thing', Field('name'))
#
## always commit your models to avoid problems later
#
# db.commit()
#
def get_user_email():
    return auth.current_user.get('email')

db.define_table(
    'person',
    Field('user_email', default=get_user_email),
    Field('first_name'),
    Field('last_name'),
)

db.define_table(
    'phone',
    Field('number'),
    Field('name'),
    Field('person_id', required=True),
)

db.person.id.readable = False
db.person.user_email.readable = False


db.commit()
