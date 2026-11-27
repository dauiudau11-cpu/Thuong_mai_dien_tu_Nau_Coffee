"""Anonymized development snapshot replay; all writes restricted to guarded test DB."""
import json
from pathlib import Path
from django.contrib.auth.models import Group, User
from django.core import serializers
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from config.test_runner import validate_test_target, ACCOUNTS_QA_IDENTITY, verify_qa_identity

FIXTURE = Path(__file__).parent / 'fixtures' / 'pickup_compatibility.json'


def load_compatibility_fixture():
    validate_test_target(connection.settings_dict, keepdb=True, parallel=1)
    if connection.vendor != 'postgresql':
        raise ImproperlyConfigured('Snapshot replay requires guarded PostgreSQL test DB.')
    if (connection.settings_dict['NAME'], connection.settings_dict['USER']) == ACCOUNTS_QA_IDENTITY:
        verify_qa_identity(connection)
    with connection.cursor() as cursor:
        cursor.execute('SELECT current_database(), current_user')
        if cursor.fetchone() != (connection.settings_dict['NAME'], connection.settings_dict['USER']):
            raise ImproperlyConfigured('Refusing snapshot replay on any other database.')
    # A TestCase/TransactionTestCase owns rollback/cleanup; never flush or overwrite data here.
    from catalog.models import Product
    from commerce.models import Order
    if Product.objects.exists() or Order.objects.exists():
        raise ImproperlyConfigured('Snapshot replay requires an empty test fixture scope.')
    payload = json.loads(FIXTURE.read_text())
    if payload.get('format') != 'nau-pickup-anonymized-v1' or not all(payload['source_checks'].values()):
        raise ImproperlyConfigured('Unverified compatibility fixture.')
    for role in ['CUSTOMER', 'STAFF', 'ADMIN']:
        Group.objects.get_or_create(name=role)
    for pk in payload['user_ids']:
        user = User(id=pk, username=f'historical-fixture-{pk}')
        user.set_unusable_password()
        user.save()
        user.groups.add(Group.objects.get(name='CUSTOMER'))
    for entry in serializers.deserialize('json', json.dumps(payload['objects'])):
        entry.save()
    from django.apps import apps
    from django.core.management.color import no_style
    labels = {row['model'] for row in payload['objects']} | {'auth.user', 'auth.group'}
    with connection.cursor() as cursor:
        for sql in connection.ops.sequence_reset_sql(no_style(), [apps.get_model(label) for label in labels]):
            cursor.execute(sql)
    return payload


def create_role_user(username, role, password='Browser-testing-823!'):
    # Snapshot PKs were inserted explicitly; choose an unused PK independent of sequence position.
    from django.db.models import Max
    pk = (User.objects.aggregate(last=Max('pk'))['last'] or 0) + 1
    user = User.objects.create_user(pk=pk, username=username, password=password, is_staff=role=='ADMIN')
    user.groups.add(Group.objects.get(name=role))
    return user


def history_state():
    """Exact values of every copied historical row, excluding later orders/events."""
    from django.apps import apps
    payload=json.loads(FIXTURE.read_text())
    historical_labels=['commerce.order','commerce.orderitem','commerce.payment','commerce.paymentevent',
        'commerce.orderstatushistory','commerce.stockmovement','commerce.loyaltyledger']
    result={}
    for label in historical_labels:
        ids=[row['pk'] for row in payload['objects'] if row['model']==label]
        result[label]=list(apps.get_model(label).objects.filter(pk__in=ids).order_by('pk').values())
    return result
