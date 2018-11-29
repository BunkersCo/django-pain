"""Test admin views."""
from django.contrib import admin
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from django_pain.admin import BankPaymentAdmin
from django_pain.constants import InvoiceType, PaymentState
from django_pain.models import BankPayment
from django_pain.tests.mixins import CacheResetMixin
from django_pain.tests.utils import DummyPaymentProcessor, get_account, get_client, get_invoice, get_payment


class LinkedDummyPaymentProcessor(DummyPaymentProcessor):
    """Payment processor with link functions."""

    def get_invoice_url(self, invoice):
        """Dummy url."""
        return 'http://example.com/invoice/'

    def get_client_url(self, client):
        """Dummy url."""
        return 'http://example.com/client/'


@override_settings(ROOT_URLCONF='django_pain.tests.urls')
class TestBankAccountAdmin(TestCase):
    """Test BankAccountAdmin."""

    def setUp(self):
        self.admin = User.objects.create_superuser('admin', 'admin@example.com', 'password')
        self.account = get_account(account_number='123456/0300', currency='USD')
        self.account.save()

    def test_get_list(self):
        """Test GET request on model list."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse('admin:django_pain_bankaccount_changelist'))
        self.assertContains(response, '123456/0300')

    def test_get_add(self):
        """Test GET request on bank account add."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse('admin:django_pain_bankaccount_add'))
        self.assertContains(response, '<option value="USD">US Dollar</option>', html=True)

    def test_get_change(self):
        """Test GET request on bank account change."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse('admin:django_pain_bankaccount_change', args=(self.account.pk,)))
        self.assertContains(response, '123456/0300')
        self.assertContains(response, '<div class="readonly">USD</div>', html=True)


@override_settings(
    ROOT_URLCONF='django_pain.tests.urls',
    PAIN_PROCESSORS={'dummy': 'django_pain.tests.utils.DummyPaymentProcessor'})
class TestBankPaymentAdmin(CacheResetMixin, TestCase):
    """Test BankAccountAdmin."""

    def setUp(self):
        super().setUp()
        self.admin = User.objects.create_superuser('admin', 'admin@example.com', 'password')
        self.request_factory = RequestFactory()

        self.account = get_account(account_name='My Account')
        self.account.save()
        self.imported_payment = get_payment(
            identifier='My Payment 1', account=self.account, state=PaymentState.IMPORTED, variable_symbol='VAR1',
        )
        self.imported_payment.save()
        self.processed_payment = get_payment(
            identifier='My Payment 2', account=self.account, state=PaymentState.PROCESSED, variable_symbol='VAR2',
            processor='dummy'
        )
        self.processed_payment.save()
        self.invoice = get_invoice(number='INV111222')
        self.invoice.save()
        self.invoice.payments.add(self.processed_payment)
        self.payment_client = get_client(handle='HANDLE', payment=self.processed_payment)
        self.payment_client.save()

    def test_get_list(self):
        """Test GET request on model list."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse('admin:django_pain_bankpayment_changelist'))
        self.assertContains(response, 'VAR1')
        self.assertContains(response, 'VAR2')
        self.assertContains(response, 'INV111222')

    def test_get_detail(self):
        """Test GET request on model detail."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse('admin:django_pain_bankpayment_change', args=[self.processed_payment.pk]))
        self.assertContains(response, 'My Payment 2')
        self.assertContains(response, 'INV111222')
        self.assertContains(response, 'HANDLE')

    def test_get_fieldsets(self):
        """Test get_fieldsets method."""
        modeladmin = BankPaymentAdmin(BankPayment, admin.site)
        request = self.request_factory.get('/', {})
        request.user = self.admin

        fieldsets = modeladmin.get_fieldsets(request)
        self.assertEqual(len(fieldsets), 1)

        fieldsets = modeladmin.get_fieldsets(request, self.imported_payment)
        self.assertEqual(len(fieldsets), 2)
        self.assertEqual(fieldsets[1][1]['fields'], ('processor', 'client_id'))

        fieldsets = modeladmin.get_fieldsets(request, self.processed_payment)
        self.assertEqual(len(fieldsets), 1)


@override_settings(PAIN_PROCESSORS={
    'linked_dummy': 'django_pain.tests.admin.test_admin.LinkedDummyPaymentProcessor',
})
class TestBankPaymentAdminLinks(TestBankPaymentAdmin):
    """Test BankAccountAdmin with invoice and client links."""

    def setUp(self):
        super().setUp()
        self.processed_payment.processor = 'linked_dummy'
        self.processed_payment.save()
        self.invoice2 = get_invoice(number='INV222333', invoice_type=InvoiceType.ACCOUNT)
        self.invoice2.save()
        self.invoice2.payments.add(self.processed_payment)

    def test_get_list_links(self):
        """Test GET request on model list."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse('admin:django_pain_bankpayment_changelist'))
        self.assertContains(response, '<a href="http://example.com/invoice/">INV111222</a>&nbsp;(+1)')

    def test_get_list_no_advance_invoice(self):
        """Test GET request on model list."""
        self.invoice.invoice_type = InvoiceType.ACCOUNT
        self.invoice.save()
        self.invoice2.invoice_type = InvoiceType.ACCOUNT
        self.invoice2.save()
        self.client.force_login(self.admin)
        response = self.client.get(reverse('admin:django_pain_bankpayment_changelist'))
        self.assertContains(response, '(+2)')

    def test_get_detail_links(self):
        """Test GET request on model detail."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse('admin:django_pain_bankpayment_change', args=[self.processed_payment.pk]))
        self.assertContains(response, '<a href="http://example.com/invoice/">INV111222</a>')
        self.assertContains(response, '<a href="http://example.com/client/">HANDLE</a>')


@override_settings(ROOT_URLCONF='django_pain.tests.urls')
class TestUserAdmin(TestCase):
    """Test UserAdmin."""

    def setUp(self):
        self.admin = User.objects.create_superuser('admin', 'admin@example.com', 'password')

    def test_get_add(self):
        """Test GET request on add view."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse('admin:auth_user_add'))
        self.assertContains(
            response,
            "If you use external authentication system such as LDAP, you don't have to choose a password."
        )

    def test_post_add_password(self):
        """Test POST request on add view."""
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse('admin:auth_user_add'),
            data={'username': 'yoda', 'password1': 'usetheforce', 'password2': 'usetheforce'},
        )
        user = User.objects.get(username='yoda')
        self.assertRedirects(response, reverse('admin:auth_user_change', args=(user.pk,)))
        self.assertTrue(user.has_usable_password())

    def test_post_add_no_password(self):
        """Test POST request on add view without password."""
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse('admin:auth_user_add'),
            data={'username': 'yoda', 'password1': '', 'password2': ''},
        )
        user = User.objects.get(username='yoda')
        self.assertRedirects(response, reverse('admin:auth_user_change', args=(user.pk,)))
        self.assertFalse(user.has_usable_password())
