"""Phase-one accounts: isolated fixtures only; PostgreSQL races explicitly skip on SQLite."""
from datetime import timedelta
import io
import re
import smtplib
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless
from unittest.mock import patch
from django.contrib.auth import authenticate
from django.contrib.auth.models import User, Group
from django.core import mail
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, connection, connections, transaction
from django.test import TestCase, TransactionTestCase, Client, override_settings
from django.utils import timezone
from catalog import customer_accounts as accounts
from catalog.customer_models import CustomerProfile, CounterConsent, CounterCustomerLink
from catalog.models import Address, Category, Product, ProductVariant, ChannelPrice
from commerce.models import Ingredient, RecipeLine, StockMovement, StoreSettings, Order, LoyaltyLedger
from commerce.operations import manual_order, award_loyalty

PASSWORD = 'Customer-test-only-823!'
EMAIL_SETTINGS = dict(AUTHENTICATION_BACKENDS=['catalog.customer_auth.CustomerModelBackend'], NAU_STANDARD_MENU_ENABLED=False, NAU_CUSTOMER_ACCOUNTS_ENABLED=True, NAU_ACCOUNT_EMAIL_READY=True,
    NAU_ACCOUNT_ALLOW_TEST_EMAIL=True, EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    NAU_ACCOUNT_PUBLIC_ORIGIN='https://coffee.example.invalid', DEFAULT_FROM_EMAIL='nau@example.invalid',
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])


@override_settings(**EMAIL_SETTINGS)
class CustomerAccountTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        for role in ('CUSTOMER', 'STAFF', 'ADMIN'):
            Group.objects.create(name=role)
        cls.staff = User.objects.create_user('account-staff', password=PASSWORD)
        cls.staff.groups.add(Group.objects.get(name='STAFF'))

    def data(self, **updates):
        return dict(full_name='Khách Thử Nghiệm', phone='0901234567', email='Customer@Example.invalid',
                    username='account-customer', password1=PASSWORD, password2=PASSWORD, **updates)

    def make(self, *, verified=False, **updates):
        data = self.data(); data.update(updates)
        profile = accounts.create_customer(data)
        if verified:
            accounts.activate(accounts.token_for(profile), PASSWORD, PASSWORD)
            profile.refresh_from_db()
        return profile

    def staff_login(self):
        self.client.force_login(self.staff)

    def test_public_signup_requires_verification_and_all_six_fields(self):
        response = self.client.post('/accounts/register/', self.data())
        self.assertEqual(response.status_code, 200)
        profile = CustomerProfile.objects.get()
        self.assertEqual(profile.phone, '+84901234567')
        self.assertEqual(profile.email, 'customer@example.invalid')
        self.assertFalse(profile.user.is_active)
        self.assertTrue(profile.user.check_password(PASSWORD))
        self.assertEqual(list(profile.user.groups.values_list('name', flat=True)), ['CUSTOMER'])
        self.assertEqual(len(mail.outbox), 1)
        self.assertContains(response, 'Chờ bạn xác minh email')
        self.assertNotContains(response, '#token=')
        self.assertIsNone(authenticate(username=profile.user.username, password=PASSWORD))

    def test_each_required_field_is_validated(self):
        for key in self.data():
            data = self.data(); data.pop(key)
            response = self.client.post('/accounts/register/', data)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context['form'].errors, key)
        self.assertFalse(CustomerProfile.objects.exists())

    def test_duplicate_phone_normalized_and_email_case_insensitive(self):
        self.make()
        for changes, field in [({'phone': '+84 901-234-567', 'email': 'other@example.invalid'}, 'phone'),
                               ({'phone': '0901234568', 'email': 'CUSTOMER@example.invalid'}, 'email')]:
            data = self.data(); data.update(changes, username='another')
            response = self.client.post('/accounts/register/', data)
            self.assertIn(field, response.context['form'].errors)
        self.assertEqual(CustomerProfile.objects.count(), 1)

    def test_legacy_email_collision_is_not_claimed_or_rewritten(self):
        old = User.objects.create_user('legacy-conflict', email='CUSTOMER@EXAMPLE.INVALID', password=PASSWORD)
        User.objects.filter(pk=old.pk).update(email=' CUSTOMER@EXAMPLE.INVALID ')
        with self.assertRaises(ValidationError): accounts.create_customer(self.data())
        old.refresh_from_db(); self.assertTrue(old.is_active)
        self.assertFalse(CustomerProfile.objects.exists())

    def test_vietnamese_phone_format_validation(self):
        for value in ('0901234567', '+84901234567', '0084901234567', '(090) 123-4567'):
            self.assertEqual(accounts.normalize_phone(value), '+84901234567')
        self.assertEqual(accounts.normalize_phone('02812345678'), '+842812345678')
        for value in ('', '²', '０９０１２３４５６７', '+840901234567', '090123456', '19001234', '+1 901234567', '090<script>'):
            with self.subTest(value=value), self.assertRaises(ValidationError): accounts.normalize_phone(value)

    def test_db_constraints_reject_duplicate_or_noncanonical_phone_and_email(self):
        profile = self.make()
        other = User.objects.create_user('other-db')
        for phone, email in [(profile.phone, 'other@example.invalid'), ('+84901234568', profile.email),
                             ('0901234568', 'other@example.invalid'), ('+84901234568', 'UPPER@example.invalid'),
                             ('+84901234568', ' space@example.invalid ')]:
            with self.subTest(phone=phone), self.assertRaises(IntegrityError), transaction.atomic():
                CustomerProfile.objects.create(user=other, full_name='Khách Khác', phone=phone, email=email, origin='PUBLIC')

    def test_staff_lookup_matches_normalized_number_and_optional_addresses(self):
        profile = self.make(verified=True)
        Address.objects.create(user=profile.user, label='Nhà thử', recipient='Khách', phone='0901234567', text='Địa chỉ giả lập')
        self.staff_login()
        response = self.client.post('/dashboard/customers/lookup/', {'phone': '0901234567'})
        self.assertContains(response, profile.full_name)
        self.assertNotContains(response, 'Địa chỉ giả lập')
        self.assertContains(self.client.post('/dashboard/customers/lookup/', {'phone': '+84901234567', 'include_addresses': 'on'}), 'Địa chỉ giả lập')
        self.assertNotIn('password', response.content.decode())

    def test_lookup_unknown_and_invalid_phone(self):
        self.staff_login()
        self.assertContains(self.client.post('/dashboard/customers/lookup/', {'phone': '0901234567'}), 'Chưa tìm thấy khách phù hợp')
        self.assertTrue(self.client.post('/dashboard/customers/lookup/', {'phone': '²'}).context['form'].errors)

    def test_lookup_and_creation_are_not_public_or_customer_accessible(self):
        profile = self.make(verified=True)
        for path in ('/dashboard/customers/lookup/', '/dashboard/customers/create/'):
            self.assertEqual(self.client.post(path, {'phone': profile.phone}).status_code, 302)
            self.client.force_login(profile.user)
            self.assertEqual(self.client.post(path, {'phone': profile.phone}).status_code, 403)
            self.client.logout()

    def test_lookup_rate_limit_and_csrf(self):
        self.staff_login()
        for _ in range(20): self.client.post('/dashboard/customers/lookup/', {'phone': '0901234567'})
        self.assertEqual(self.client.post('/dashboard/customers/lookup/', {'phone': '0901234567'}).status_code, 429)
        client = Client(enforce_csrf_checks=True);client.force_login(self.staff)
        self.assertEqual(client.post('/dashboard/customers/lookup/', {'phone': '0901234567'}).status_code, 403)

    def test_staff_created_account_has_unusable_password_and_customer_role_only(self):
        self.staff_login()
        data = self.data(); data.update(is_active=True, is_staff=True, is_superuser=True, groups='ADMIN', password=PASSWORD)
        response = self.client.post('/dashboard/customers/create/', data)
        self.assertEqual(response.status_code, 200)
        profile = CustomerProfile.objects.get()
        self.assertEqual(profile.created_by, self.staff)
        self.assertFalse(profile.user.is_active)
        self.assertFalse(profile.user.is_staff or profile.user.is_superuser or profile.user.has_usable_password())
        self.assertEqual(list(profile.user.groups.values_list('name', flat=True)), ['CUSTOMER'])
        self.assertNotContains(response, '#token=')
        self.assertNotContains(response, PASSWORD)

    def test_staff_duplicate_creation_does_not_duplicate_or_send_again(self):
        self.staff_login()
        self.client.post('/dashboard/customers/create/', self.data())
        self.client.post('/dashboard/customers/create/', self.data())
        self.assertEqual(CustomerProfile.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_email_success_failure_and_unconfigured_do_not_fake_success(self):
        profile = self.make()
        self.assertEqual(accounts.send_activation(profile.user_id), 'sent')
        self.assertIn('/accounts/activate/#token=', mail.outbox[0].body)
        self.assertIn(profile.user.username, mail.outbox[0].body)
        self.assertEqual(accounts.send_activation(profile.user_id), 'throttled')
        CustomerProfile.objects.filter(pk=profile.pk).update(last_email_attempt=None)
        with patch('django.core.mail.message.EmailMessage.send', side_effect=smtplib.SMTPException('test')):
            self.assertEqual(accounts.send_activation(profile.user_id), 'failed')
        with override_settings(NAU_ACCOUNT_EMAIL_READY=False):
            self.assertEqual(accounts.send_activation(profile.user_id), 'unavailable')
        with override_settings(EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend'), patch('builtins.print') as output:
            self.assertEqual(accounts.send_activation(profile.user_id), 'unavailable')
            output.assert_not_called()
        profile.user.refresh_from_db();self.assertFalse(profile.user.is_active)

    def test_failed_signup_email_keeps_one_pending_account_and_shows_real_status(self):
        with patch('django.core.mail.message.EmailMessage.send', side_effect=OSError('test')):
            response = self.client.post('/accounts/register/', self.data())
        self.assertContains(response, 'Chưa gửi được email')
        self.assertEqual(CustomerProfile.objects.count(), 1)
        self.assertFalse(CustomerProfile.objects.get().user.is_active)

    def test_staff_activation_sets_customer_password_and_token_is_single_use(self):
        profile = accounts.create_customer(self.data(), actor=self.staff)
        self.assertFalse(profile.user.has_usable_password())
        token = accounts.token_for(profile)
        response = self.client.post('/accounts/activate/', {'token': token, 'new_password1': PASSWORD, 'new_password2': PASSWORD})
        self.assertContains(response, 'Email đã được xác minh')
        profile.user.refresh_from_db();self.assertTrue(profile.user.is_active)
        self.assertTrue(profile.user.check_password(PASSWORD))
        self.assertIsNotNone(authenticate(username=profile.user.username, password=PASSWORD))
        with self.assertRaises(ValidationError): accounts.activate(token, PASSWORD, PASSWORD)

    def test_expired_or_tampered_activation_and_password_validation(self):
        profile = self.make();token = accounts.token_for(profile)
        with patch('django.core.signing.time.time', return_value=time.time()+86410):
            with self.assertRaises(ValidationError): accounts.activate(token, PASSWORD, PASSWORD)
        for token_value in ('bad', token+'x'):
            with self.assertRaises(ValidationError): accounts.activate(token_value, PASSWORD, PASSWORD)
        response = self.client.post('/accounts/activate/', {'token': token, 'new_password1': 'short', 'new_password2': 'different'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        profile.user.refresh_from_db();self.assertFalse(profile.user.is_active)

    def test_resend_invalidates_old_token_and_limits_attempts(self):
        profile = self.make();old = accounts.token_for(profile)
        self.assertEqual(accounts.send_activation(profile.user_id), 'sent')
        with self.assertRaises(ValidationError): accounts.activate(old, PASSWORD, PASSWORD)
        token = re.search(r'#token=(\S+)', mail.outbox[-1].body)[1]
        accounts.activate(token, PASSWORD, PASSWORD)
        self.assertEqual(accounts.send_activation(profile.user_id), 'not_pending')

    def test_public_resend_response_does_not_enumerate_accounts(self):
        self.make()
        known = self.client.post('/accounts/activation/resend/', {'email': 'customer@example.invalid'})
        unknown = self.client.post('/accounts/activation/resend/', {'email': 'unknown@example.invalid'})
        self.assertEqual(known.context['delivery_message'], unknown.context['delivery_message'])
        with override_settings(NAU_ACCOUNT_EMAIL_READY=False):
            self.assertContains(self.client.post('/accounts/activation/resend/', {'email':'unknown@example.invalid'}), 'chưa sẵn sàng')

    def test_legacy_login_completion_requires_password_and_preserves_login(self):
        old = User.objects.create_user('legacy-customer', email='', password=PASSWORD)
        old.groups.add(Group.objects.get(name='CUSTOMER'))
        Address.objects.create(user=old, label='Cũ', recipient='Cũ', phone='0908888888', text='Địa chỉ giả lập')
        self.assertIsNotNone(authenticate(username=old.username, password=PASSWORD))
        self.client.force_login(old)
        response = self.client.get('/account/profile/')
        self.assertEqual(response.context['form'].initial['phone'], '')
        data = self.data();data['current_password'] = 'wrong'
        self.assertTrue(self.client.post('/account/profile/', data).context['form'].errors)
        self.assertFalse(CustomerProfile.objects.filter(user=old).exists())
        data['current_password'] = PASSWORD
        response = self.client.post('/account/profile/', data)
        self.assertEqual(response.status_code, 200)
        old.refresh_from_db();self.assertTrue(old.is_active);self.assertEqual(old.email, '')
        profile = CustomerProfile.objects.get(user=old)
        accounts.activate(accounts.token_for(profile))
        old.refresh_from_db();self.assertEqual(old.email, 'customer@example.invalid')
        self.assertTrue(old.check_password(PASSWORD))
        self.assertIsNotNone(authenticate(username=old.username, password=PASSWORD))

    def test_contact_updates_require_reauth_email_confirmation_and_keep_current_until_confirmed(self):
        profile = self.make(verified=True);old = profile.phone
        data = dict(full_name='Tên Mới', phone='0901234568', email='new@example.invalid', current_password=PASSWORD)
        accounts.request_contact_change(profile.user, data)
        profile.refresh_from_db();self.assertEqual(profile.phone, old)
        accounts.activate(accounts.token_for(profile))
        profile.refresh_from_db();self.assertEqual(profile.phone, '+84901234568')
        self.assertEqual(profile.email, 'new@example.invalid')

    def test_contact_conflict_on_confirmation_does_not_overwrite_other_customer(self):
        profile = self.make(verified=True)
        data = dict(full_name='Tên Mới', phone='0901234568', email='new@example.invalid', current_password=PASSWORD)
        accounts.request_contact_change(profile.user, data)
        profile.refresh_from_db();token = accounts.token_for(profile)
        other = self.make(verified=True, username='other', phone='0901234568', email='new@example.invalid')
        with self.assertRaises(ValidationError): accounts.activate(token)
        profile.refresh_from_db();self.assertEqual(profile.phone, '+84901234567')
        self.assertEqual(other.phone, '+84901234568')

    def test_disabled_feature_does_not_query_new_tables(self):
        with override_settings(NAU_CUSTOMER_ACCOUNTS_ENABLED=False), patch.object(CustomerProfile, 'objects') as manager:
            self.assertEqual(self.client.get('/dashboard/customers/lookup/').status_code, 404)
            self.assertEqual(self.client.get('/accounts/register/').status_code, 200)
            manager.assert_not_called()

    def test_read_only_preflight_contains_counts_not_customer_information(self):
        profile = self.make();output = io.StringIO()
        call_command('audit_customer_accounts', stdout=output)
        self.assertIn('"writes_performed": false', output.getvalue())
        self.assertNotIn(profile.email, output.getvalue())
        self.assertNotIn(profile.phone, output.getvalue())

    def test_unverified_public_identity_cannot_login_after_active_flag_only(self):
        profile = self.make()
        User.objects.filter(pk=profile.user_id).update(is_active=True)
        self.assertIsNone(authenticate(username=profile.user.username, password=PASSWORD))

    def test_signup_rejects_invalid_names_email_and_password_confirmation(self):
        for changes in ({'full_name': 'x'}, {'email':'not-email'}, {'password2':'different'}):
            data=self.data();data.update(changes)
            response=self.client.post('/accounts/register/',data)
            self.assertTrue(response.context['form'].errors)
        self.assertFalse(CustomerProfile.objects.exists())

    def test_code_requires_verified_customer_password_and_is_hashed(self):
        profile = self.make()
        with self.assertRaises(ValidationError): accounts.issue_counter_consent(profile.user, PASSWORD)
        accounts.activate(accounts.token_for(profile), PASSWORD, PASSWORD)
        profile.user.refresh_from_db()
        with self.assertRaises(ValidationError): accounts.issue_counter_consent(profile.user, 'wrong')
        code = accounts.issue_counter_consent(profile.user, PASSWORD)
        self.assertNotEqual(CounterConsent.objects.get(user=profile.user).code_hash, code)
        self.assertEqual(self.client.get('/account/counter-consent/').status_code, 302)


@override_settings(**EMAIL_SETTINGS)
class CounterCustomerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        for role in ('CUSTOMER', 'STAFF'):Group.objects.create(name=role)
        cls.staff = User.objects.create_user('counter-staff', password=PASSWORD)
        cls.staff.groups.add(Group.objects.get(name='STAFF'))
        cls.profile = accounts.create_customer(dict(full_name='Khách Quầy', phone='0901234567', email='counter@example.invalid', username='counter-customer', password1=PASSWORD))
        accounts.activate(accounts.token_for(cls.profile), PASSWORD, PASSWORD)
        cls.profile.refresh_from_db();cls.profile.user.refresh_from_db()
        category = Category.objects.create(name='Fixture', slug='counter-fixture')
        product = Product.objects.create(category=category, code='FIX', name='Món thử', slug='counter-drink')
        cls.variant = ProductVariant.objects.create(product=product, sku='COUNTER-FIX', size='STANDARD', volume_ml=360)
        for channel, price in [('WEB',28000),('COUNTER',28000),('APP',37000)]:
            ChannelPrice.objects.create(variant=cls.variant, channel=channel, original_price=price)
        ingredient = Ingredient.objects.create(sku='FIX-CUP', name='Cốc thử', unit='piece')
        RecipeLine.objects.create(variant=cls.variant, ingredient=ingredient, quantity=1)
        StockMovement.objects.create(ingredient=ingredient, delta=1000, reason='PURCHASE', actor=cls.staff, idempotency_key='fixture-stock')
        StoreSettings.objects.get_or_create(pk=1)

    def data(self, **updates):
        values = dict(channel='COUNTER', customer_name='Khách vãng lai', phone='0901234567', idempotency_key=uuid.uuid4())
        values.update(updates);return values

    def lines(self):return [dict(variant=self.variant, quantity=1, options=[])]

    def linked_data(self):
        return self.data(customer_selection_context='fixture-staff-session', customer_selection=accounts.selection_for(self.profile, self.staff, session_context='fixture-staff-session'), confirm_customer=True,
                         customer_consent=accounts.issue_counter_consent(self.profile.user, PASSWORD))

    def place(self, data):
        with patch('commerce.operations.scheduled_slot', return_value=timezone.now()+timedelta(hours=1)):
            return manual_order(self.staff, data, self.lines())

    def test_counter_link_uses_customer_consent_and_records_staff_actor(self):
        data = self.linked_data();order = self.place(data)
        self.assertEqual(order.user_id, self.profile.user_id)
        self.assertEqual(order.customer_name, self.profile.full_name)
        self.assertEqual(order.phone, self.profile.phone)
        audit = CounterCustomerLink.objects.get(order=order)
        self.assertEqual(audit.actor, self.staff)
        self.assertEqual(audit.customer, self.profile.user)
        self.assertEqual(order.payment.status, 'UNPAID')
        self.assertEqual(self.place(data), order)  # Idempotent retry doesn't spend another code.
        with self.assertRaises(ValidationError): self.place(self.data(**{k:v for k,v in data.items() if k != 'idempotency_key'}))

    def test_phone_or_name_without_consent_never_links(self):
        order = self.place(self.data(customer_name=self.profile.full_name))
        self.assertIsNone(order.user_id)
        self.assertFalse(CounterCustomerLink.objects.filter(order=order).exists())
        self.assertFalse(LoyaltyLedger.objects.filter(order=order).exists())

    def test_wrong_or_missing_code_mismatched_phone_and_forged_selection_rejected(self):
        for mutation in ({'customer_consent':''}, {'customer_consent':'wrong'}, {'phone':'0901234568'},
                         {'customer_selection':'forged'}, {'confirm_customer':False}):
            data = self.linked_data();data.update(mutation)
            with self.subTest(mutation=mutation), self.assertRaises(ValidationError):self.place(data)
        self.assertFalse(Order.objects.exists())

    def test_bare_id_cannot_associate_customer(self):
        with self.assertRaises(ValidationError):self.place(self.data(user_id=self.profile.user_id))
        self.assertFalse(Order.objects.exists())

    def test_selection_bound_to_staff_and_expired_consent_rejected(self):
        data = self.linked_data()
        data['customer_selection'] = accounts.selection_for(self.profile, self.profile.user, session_context='fixture-staff-session')
        with self.assertRaises(ValidationError):self.place(data)
        data = self.linked_data();CounterConsent.objects.update(expires_at=timezone.now()-timedelta(seconds=1))
        with self.assertRaises(ValidationError):self.place(data)

    def test_another_customers_valid_code_cannot_link_selected_customer(self):
        other = accounts.create_customer(dict(full_name='Khách Khác', phone='0901234568', email='other@example.invalid', username='other-counter', password1=PASSWORD))
        accounts.activate(accounts.token_for(other), PASSWORD, PASSWORD);other.user.refresh_from_db()
        data = self.linked_data();data['customer_consent'] = accounts.issue_counter_consent(other.user, PASSWORD)
        with self.assertRaises(ValidationError):self.place(data)
        self.assertFalse(Order.objects.exists())

    def test_guest_counter_and_app_behavior_remains_unlinked_with_channel_price(self):
        guest = self.place(self.data());self.assertIsNone(guest.user_id);self.assertEqual(guest.total,28000)
        app = self.place(self.data(channel='APP', external_reference='fixture-app'))
        self.assertIsNone(app.user_id);self.assertEqual(app.total,37000)
        self.assertEqual(app.payment.method, 'EXTERNAL_DEMO')
        data = self.linked_data();data.update(channel='APP', external_reference='forged-app')
        with self.assertRaises(ValidationError):self.place(data)

    def test_failed_business_validation_rolls_back_consent_use_and_order_link(self):
        data=self.linked_data()
        with patch('commerce.operations.check_order_inventory', side_effect=ValidationError('BOM test')):
            with self.assertRaises(ValidationError):self.place(data)
        self.assertIsNone(CounterConsent.objects.get(user=self.profile.user).used_at)
        self.assertFalse(Order.objects.exists())

    def test_http_lookup_pos_explicit_confirmation_and_clear_selection(self):
        self.client.force_login(self.staff)
        self.client.post('/dashboard/customers/lookup/', {'phone':'0901234567'})
        response=self.client.get('/dashboard/orders/new-manual/')
        self.assertEqual(response.status_code,200)
        self.assertContains(response, 'Mã đồng ý dùng một lần')
        data=dict(channel='COUNTER',customer_name='Nhập tay',phone='0901234567',
            idempotency_key=self.client.session['manual_order_key'],
            customer_selection=self.client.session['counter_customer_selection'],
            customer_consent=accounts.issue_counter_consent(self.profile.user,PASSWORD),
            **{'lines-TOTAL_FORMS':'1','lines-INITIAL_FORMS':'0','lines-MIN_NUM_FORMS':'1',
               'lines-MAX_NUM_FORMS':'10','lines-0-variant':str(self.variant.pk),'lines-0-quantity':'1'})
        with patch('commerce.operations.scheduled_slot',return_value=timezone.now()+timedelta(hours=1)):
            response=self.client.post('/dashboard/orders/new-manual/',data)
            self.assertEqual(response.status_code,200);self.assertFalse(Order.objects.exists())
            data['confirm_customer']='on'
            response=self.client.post('/dashboard/orders/new-manual/',data)
            self.assertEqual(response.status_code,302)
        self.assertEqual(Order.objects.get().user_id,self.profile.user_id)
        self.assertNotIn('counter_customer_selection',self.client.session)
        self.client.post('/dashboard/customers/lookup/', {'phone':'0901234567'})
        self.assertEqual(self.client.post('/dashboard/customers/clear/').status_code,302)
        self.assertNotIn('counter_customer_selection',self.client.session)

    def test_selection_rejects_other_session_without_spending_consent(self):
        from django.core import signing
        data=self.linked_data()
        data['customer_selection']=signing.dumps(dict(uid=self.profile.user_id,phone=self.profile.phone,
            actor=self.staff.pk,session='session-one',purpose='COUNTER_CUSTOMER_LINK'),salt=accounts.SELECTION_SALT)
        data['customer_selection_context']='session-two'
        with self.assertRaises(ValidationError):self.place(data)
        self.assertIsNone(CounterConsent.objects.get(user=self.profile.user).used_at)
        self.assertFalse(Order.objects.exists())

    def test_selection_requires_context_and_expires(self):
        for context in ('',None):
            data=self.linked_data();data['customer_selection_context']=context
            with self.assertRaises(ValidationError):self.place(data)
        data=self.linked_data()
        with patch('django.core.signing.time.time',return_value=time.time()+310):
            with self.assertRaises(ValidationError):self.place(data)
        self.assertFalse(Order.objects.exists())
        self.assertIsNone(CounterConsent.objects.get(user=self.profile.user).used_at)

    def test_selection_rejects_wrong_purpose(self):
        from django.core import signing
        data=self.linked_data()
        data['customer_selection']=signing.dumps(dict(uid=self.profile.user_id,phone=self.profile.phone,
            actor=self.staff.pk,session='session-one',purpose='EMAIL_ACTIVATE'),salt=accounts.SELECTION_SALT)
        data['customer_selection_context']='session-one'
        with self.assertRaises(ValidationError):self.place(data)
        self.assertIsNone(CounterConsent.objects.get(user=self.profile.user).used_at)

    def test_http_selection_from_another_session_is_not_accepted_even_with_posted_context(self):
        self.client.force_login(self.staff)
        self.client.post('/dashboard/customers/lookup/',{'phone':'0901234567'})
        copied=self.client.session['counter_customer_selection']
        other=Client();other.force_login(self.staff)
        other.post('/dashboard/customers/lookup/',{'phone':'0901234567'})
        other.get('/dashboard/orders/new-manual/')
        data=dict(channel='COUNTER',customer_name='Fixture',phone='0901234567',
            idempotency_key=other.session['manual_order_key'],customer_selection=copied,
            customer_selection_context=self.client.session.get('counter_selection_context','forged'),
            customer_consent=accounts.issue_counter_consent(self.profile.user,PASSWORD),confirm_customer='on',
            **{'lines-TOTAL_FORMS':'1','lines-INITIAL_FORMS':'0','lines-MIN_NUM_FORMS':'1',
               'lines-MAX_NUM_FORMS':'10','lines-0-variant':str(self.variant.pk),'lines-0-quantity':'1'})
        with patch('commerce.operations.scheduled_slot',return_value=timezone.now()+timedelta(hours=1)):
            response=other.post('/dashboard/orders/new-manual/',data)
        self.assertEqual(response.status_code,200)
        self.assertFalse(Order.objects.exists())
        self.assertIsNone(CounterConsent.objects.get(user=self.profile.user).used_at)

    def test_verified_customer_web_checkout_remains_pickup_mock_online(self):
        self.client.force_login(self.profile.user)
        self.client.post('/cart/add/', {'variant':self.variant.pk,'quantity':1})
        response=self.client.get('/checkout/')
        self.assertEqual(response.status_code,200)
        data=dict(customer_name=self.profile.full_name,phone='0901234567',fulfillment='PICKUP',
            payment_method='MOCK_ONLINE',accept_demo='on',action='place',
            idempotency_key=self.client.session['checkout_key'])
        with patch('commerce.operations.scheduled_slot',return_value=timezone.now()+timedelta(hours=1)):
            response=self.client.post('/checkout/',data)
        self.assertEqual(response.status_code,302)
        order=Order.objects.get(user=self.profile.user)
        self.assertEqual(order.fulfillment,'PICKUP')
        self.assertEqual(order.payment.method,'MOCK_ONLINE')
        self.assertEqual(order.payment.status,'PENDING')
        self.assertFalse(CounterCustomerLink.objects.filter(order=order).exists())

    def test_admin_review_integer_filters_still_work_with_accounts_enabled(self):
        from support.models import Review
        for rating in (1,5):
            order=self.place(self.data())
            Review.objects.create(user=self.profile.user,product=self.variant.product,
                item=order.items.first(),rating=rating,body='Kiểm thử bộ lọc',status='PENDING')
        admin=User.objects.create_superuser('accounts-admin','admin@example.invalid',PASSWORD)
        self.client.force_login(admin)
        for path in ('/admin/support/review/','/admin/support/review/?rating=5',
                     '/admin/support/message/','/admin/catalog/product/add/','/admin/auth/user/add/'):
            self.assertEqual(self.client.get(path).status_code,200,path)

    def test_no_sensitive_loyalty_for_unlinked_guest_even_after_completion(self):
        guest=self.place(self.data());guest.status='COMPLETED';guest.save()
        guest.payment.status='PAID';guest.payment.save()
        award_loyalty(guest)
        self.assertFalse(LoyaltyLedger.objects.filter(order=guest).exists())


@skipUnless(connection.vendor == 'postgresql', 'Requires independently attested PostgreSQL QA; SQLite is not race evidence.')
@override_settings(**EMAIL_SETTINGS)
class CustomerIdentityConcurrencyTests(TransactionTestCase):
    def test_two_requests_cannot_create_duplicate_normalized_phone(self):
        Group.objects.create(name='CUSTOMER')
        barrier=Barrier(2);original=accounts.validate_identity
        def validate(*args, **kwargs):
            result=original(*args, **kwargs);barrier.wait(timeout=15);return result
        def create(index):
            try:
                accounts.create_customer(dict(full_name='Khách Race', phone='0901234567' if index==0 else '+84901234567',
                    email=f'race{index}@example.invalid', username=f'race-{index}', password1=PASSWORD))
                return 'created'
            except IntegrityError:return 'conflict'
            finally:connections.close_all()
        with patch('catalog.customer_accounts.validate_identity', side_effect=validate), ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(create, range(2)))
        self.assertCountEqual(results, ['created','conflict'])
        self.assertEqual(CustomerProfile.objects.count(),1)
        self.assertEqual(User.objects.filter(username__startswith='race-').count(),1)

    def test_two_staff_requests_cannot_spend_the_same_customer_consent(self):
        CounterCustomerTests.setUpTestData.__func__(type(self))
        second=User.objects.create_user('counter-second-staff',password=PASSWORD)
        second.groups.add(Group.objects.get(name='STAFF'))
        code=accounts.issue_counter_consent(self.profile.user,PASSWORD)
        barrier=Barrier(2);actors=[self.staff,second]
        def create(index):
            try:
                actor=actors[index];context=f'concurrent-session-{index}'
                data=dict(channel='COUNTER',customer_name='Khách kiểm thử',phone=self.profile.phone,
                    idempotency_key=uuid.uuid4(),confirm_customer=True,customer_consent=code,
                    customer_selection_context=context,
                    customer_selection=accounts.selection_for(self.profile,actor,session_context=context))
                barrier.wait(timeout=15)
                manual_order(actor,data,[dict(variant=self.variant,quantity=1,options=[])])
                return 'created'
            except ValidationError:return 'rejected'
            finally:connections.close_all()
        with patch('commerce.operations.scheduled_slot',return_value=timezone.now()+timedelta(hours=1)), ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(create,range(2)))
        self.assertCountEqual(results,['created','rejected'])
        self.assertEqual(Order.objects.count(),1)
        self.assertEqual(CounterCustomerLink.objects.count(),1)
        self.assertIsNotNone(CounterConsent.objects.get(user=self.profile.user).used_at)


class CustomerMigrationCompatibilityTests(TransactionTestCase):
    def test_new_tables_preserve_legacy_users_duplicate_emails_and_order(self):
        from django.db.migrations.executor import MigrationExecutor
        target=('catalog','0005_counterconsent_countercustomerlink_customerprofile')
        previous=[('catalog','0004_alter_productvariant_size_standardcost'),('commerce','0004_demo_delivery')]
        executor=MigrationExecutor(connection)
        executor.migrate(previous)
        try:
            old=executor.loader.project_state(previous).apps
            OldUser=old.get_model('auth','User');OldOrder=old.get_model('commerce','Order')
            first=OldUser.objects.create(username='migration-legacy-1',email='SHARED@example.invalid',is_active=True)
            OldUser.objects.create(username='migration-legacy-2',email='shared@example.invalid',is_active=True)
            OldUser.objects.create(username='migration-no-contact',email='',is_active=True)
            order=OldOrder.objects.create(user=first,channel='COUNTER',fulfillment='PICKUP',customer_name='Lịch sử',
                phone='không tự chuẩn hóa',subtotal=28000,total=28000,status='COMPLETED',idempotency_key=uuid.uuid4())
            before_users=list(OldUser.objects.order_by('pk').values())
            before_order=OldOrder.objects.values().get(pk=order.pk)
            output=io.StringIO();call_command('audit_customer_accounts',stdout=output)
            import json
            audit=json.loads(output.getvalue())
            self.assertEqual(audit['case_insensitive_email_conflict_groups'],1)
            self.assertFalse(audit['profile_schema_present'])
            self.assertFalse(audit['writes_performed'])
        finally:
            executor=MigrationExecutor(connection);executor.migrate(executor.loader.graph.leaf_nodes())
        self.assertEqual(list(User.objects.order_by('pk').values()),before_users)
        self.assertEqual(Order.objects.values().get(pk=order.pk),before_order)
        self.assertEqual(CustomerProfile.objects.count(),0)

    def test_migration_on_empty_application_schema(self):
        from django.db.migrations.executor import MigrationExecutor
        target=('catalog','0005_counterconsent_countercustomerlink_customerprofile')
        previous=[('catalog','0004_alter_productvariant_size_standardcost'),('commerce','0004_demo_delivery')]
        executor=MigrationExecutor(connection);executor.migrate(previous)
        try:
            self.assertFalse(User.objects.exists())
            self.assertFalse(Order.objects.exists())
        finally:
            executor=MigrationExecutor(connection);executor.migrate(executor.loader.graph.leaf_nodes())
        self.assertEqual(CustomerProfile.objects.count(),0)
        self.assertEqual(CounterConsent.objects.count(),0)
        self.assertEqual(CounterCustomerLink.objects.count(),0)
        with connection.cursor() as cursor:
            constraints=connection.introspection.get_constraints(cursor,'catalog_customerprofile')
        self.assertTrue(constraints['customer_email_ci_unique']['unique'])
        self.assertTrue(constraints['customer_phone_canonical']['check'])
