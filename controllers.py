"""
This file defines actions, i.e. functions the URLs are mapped into
The @action(path) decorator exposed the function at URL:

    http://127.0.0.1:8000/{app_name}/{path}

If app_name == '_default' then simply

    http://127.0.0.1:8000/{path}

If path == 'index' it can be omitted:

    http://127.0.0.1:8000/

The path follows the bottlepy syntax.

@action.uses('generic.html')  indicates that the action uses the generic.html template
@action.uses(session)         indicates that the action uses the session
@action.uses(db)              indicates that the action uses the db
@action.uses(T)               indicates that the action uses the i18n & pluralization
@action.uses(auth.user)       indicates that the action requires a logged in user
@action.uses(auth)            indicates that the action requires the auth object

session, db, T, auth, and tempates are examples of Fixtures.
Warning: Fixtures MUST be declared with @action.uses({fixtures}) else your app will result in undefined behavior
"""

import uuid

from py4web import action, request, abort, redirect, URL, Field
from py4web.utils.form import Form, FormStyleBulma
from py4web.utils.url_signer import URLSigner

from yatl.helpers import A
from . common import db, session, T, cache, auth, signed_url


url_signer = URLSigner(session)

# The auth.user below forces login.
@action('index')
@action.uses('index.html', auth.user, db, session)
def index():
    user = auth.current_user.get('email')
    
    rows = db(db.person.user_email == user).select().as_list()
    # rows = db().select().as_list()
    #onc as list, must use brackets
    for index, row in enumerate(rows):
        person_id = row["id"]
        phone_numbers = db(db.phone.person_id == person_id).select().as_list()
        formatted_nums = ""
        for index2, phone_number in enumerate(phone_numbers):
            formatted_nums += phone_number["number"]
            formatted_nums += "(" + phone_number["name"]+ ")"
            if(index2 + 1 != len(phone_numbers)):
                formatted_nums += ", "
        rows[index]["phone_numbers"] = formatted_nums

    return dict(rows=rows, url_signer=url_signer)


@action('add_contact', method=['GET', 'POST'])
@action.uses('contact_form.html', session, db, auth.user)
def add_product():
    form = Form(db.person, csrf_session=session, formstyle=FormStyleBulma)
    if form.accepted:
        # We always want POST requests to be redirected as GETs.
        redirect(URL('index'))
    return dict(form=form)

@action('edit_person/<person_id>', method=['GET', 'POST'])
@action.uses('contact_form.html', session, db, auth.user, signed_url)
def edit_product(person_id=None):
    """Note that in the above declaration, the product_id argument must match
    the <product_id> argument of the @action."""
    # We read the product.
    
    p = db.person[person_id]
    if p is None:
        # Nothing to edit.  This should happen only if you tamper manually with the URL.
        redirect(URL('index'))
    email = auth.current_user.get('email')
    if db.person[person_id].user_email != email:
        redirect(URL('index'))
    
    form = Form(db.person, record=p, deletable=False, csrf_session=session, formstyle=FormStyleBulma)
    if form.accepted:
        # We always want POST requests to be redirected as GETs.
        redirect(URL('index'))
    return dict(form=form)


@action('delete_person/<person_id>', method=['GET', 'POST'])
@action.uses('contact_form.html', session, db, url_signer.verify(), auth.user) #
def delete_product(person_id=None):
    """Note that in the above declaration, the product_id argument must match
    the <product_id> argument of the @action."""
    # We read the product.
    p = db.person[person_id]
    if p is None:
        # Nothing to edit.  This should happen only if you tamper manually with the URL.
        redirect(URL('index'))
    
    db(db.person.id == person_id).delete()
    deleted = db.person[person_id]
    if deleted is None:
        redirect(URL('index'))

    return dict(deleted=deleted)



@action('list_phone/<person_id>', method=['GET'])
@action.uses('phone_list.html', auth.user, db, session)
def list_phone(person_id=None):


    logged_in_user = auth.current_user.get('email')
    person = db.person[person_id]
    name = person['first_name'] + " " + person['last_name']

    if person is None:
        redirect(URL('index'))
    elif(person.user_email == logged_in_user):
        row = db(db.phone.person_id == person_id).select()
        return dict(rows=row, url_signer=url_signer, person_id=person_id, name=name)
    else:
        redirect(URL('index'))



@action('add_phone/<person_id>', method=['GET', 'POST'])
@action.uses('add_phone.html', auth.user, db, session)
def add_phone(person_id=None):
    logged_in_user = auth.current_user.get('email')
    person = db.person[person_id]

    if person is None:
        redirect(URL('index'))
    elif(person.user_email == logged_in_user):
        # good part here
        form = Form([Field('number'), Field('name')],
            csrf_session=session,
            formstyle=FormStyleBulma)
        if form.accepted:
            db.phone.insert(
                number=form.vars["number"], name=form.vars["name"], person_id=person_id
            )
            redirect(URL('list_phone', person_id))
        return dict(form=form, name=person.first_name + " " + person.last_name, user=auth.user)

    else:
        redirect(URL('index'))

@action('edit_phone/<person_id>/<phone_id>', method=['GET', 'POST'])
@action.uses('add_phone.html', auth.user, db, session)
def edit_phone(person_id=None, phone_id=None):
    logged_in_user = auth.current_user.get('email')
    person = db.person[person_id]
    phone_number = db.phone[phone_id]
    if person is None:
        redirect(URL('index'))
    elif(person.user_email == logged_in_user):
        # good part here
        form = Form([Field('number'), Field('name')], record=phone_number, deletable=False,
            csrf_session=session,
            formstyle=FormStyleBulma)
        if form.accepted:
            db(db.phone.id == phone_id).update(
                number=form.vars["number"], name=form.vars["name"]
            )
            redirect(URL('list_phone', person_id))
        return dict(form=form, name=person.first_name + " " + person.last_name, user=auth.user)

    else:
        redirect(URL('index'))

@action('delete_phone/<person_id>/<phone_id>', method=['GET'])
@action.uses(session, db, url_signer.verify())
def delete_phone(person_id=None, phone_id=None):
    logged_in_user = auth.current_user.get('email')
    person = db.person[person_id]

    if person is None or phone_id is None:
        redirect(URL('index'))
    else:
        if(person.user_email == logged_in_user):
            db(db.phone.id == phone_id).delete()
        redirect(URL('list_phone', person_id))




# for list, must be [[=(row["first_name"])]]
# when adding the name, pass in the name value 
# if delete contact, delete phone numbers 