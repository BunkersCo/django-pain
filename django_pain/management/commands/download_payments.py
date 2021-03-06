#
# Copyright (C) 2020  CZ.NIC, z. s. p. o.
#
# This file is part of FRED.
#
# FRED is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# FRED is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with FRED.  If not, see <https://www.gnu.org/licenses/>.

"""Command for downloading payments from bank."""
import logging
from datetime import date, timedelta
from typing import Iterable, Optional, Tuple

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError, no_translations
from django.db import transaction
from django.db.utils import IntegrityError
from django.utils import timezone
from teller.statement import BankStatement

from django_pain.models import BankAccount, BankPayment
from django_pain.settings import SETTINGS
from django_pain.utils import parse_date_safe

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    """Download payments from banks."""

    help = 'Download payments from the banks.'
    default_interval = 7

    def add_arguments(self, parser):
        """Command takes two argument - end date and interval in days."""
        parser.add_argument('-e', '--end', type=parse_date_safe, required=False,
                            help='end date of the download interval, default: TODAY')
        parser.add_argument('-s', '--start', type=parse_date_safe, required=False,
                            help='start date of the download interval, default: END minus seven days')

    @no_translations
    def handle(self, *args, **options):
        """Run command."""
        self.options = options
        LOGGER.info('Command download_payments started.')

        start_date, end_date = self._set_dates(options['start'], options['end'])

        for key, value in SETTINGS.downloaders.items():
            LOGGER.info('Processing: {}'.format(key))

            downloader_class = value['DOWNLOADER']
            parser_class = value['PARSER']

            try:
                downloader = downloader_class(**value['DOWNLOADER_PARAMS'])
            except Exception:
                # Do not log the error message here as it may contain sensitive information such as login credentials.
                LOGGER.error('Could not init Downloader for %s.', key)
                continue
            try:
                # TODO: urllib3.connectionpool logs the URL in the DEBUG mode
                LOGGER.debug('Downloading payments for %s.', key)
                raw_statement = downloader.get_statement(start_date, end_date)
            except Exception:
                # Do not log the error message here as it may contain sensitive information such as login credentials.
                LOGGER.error('Downloading payments for %s failed.', key)
                continue

            LOGGER.debug('Parsing payments for %s.', key)
            try:
                statement = parser_class.parse_string(raw_statement)
            except Exception as e:
                LOGGER.error(str(e))
                continue

            payments = self._convert_to_models(statement)

            LOGGER.debug('Saving payments for %s.', key)
            self.save_payments(payments)

        LOGGER.info('Command download_payments finished.')

    def _set_dates(self, start_date: Optional[date], end_date: Optional[date]) -> Tuple[date, date]:
        if end_date is None:
            end_date = self._get_today()
        if start_date is None:
            start_date = end_date - timedelta(days=7)

        if start_date > end_date:
            raise CommandError('Start date has to be lower or equal to the end date.')
        return start_date, end_date

    def _get_today(self) -> date:
        if settings.USE_TZ:
            return timezone.localtime().date()
        else:
            return date.today()

    def _convert_to_models(self, statement: BankStatement) -> Iterable[BankPayment]:
        account_number = statement.account_number
        try:
            account = BankAccount.objects.get(account_number=account_number)
        except BankAccount.DoesNotExist:
            raise CommandError('Bank account {} does not exist.'.format(account_number))
        payments = []
        for payment_data in statement:
            payment = BankPayment.from_payment_data_class(payment_data)
            payment.account = account
            payments.append(payment)
        return payments

    def save_payments(self, payments: Iterable[BankPayment]) -> None:
        """Save payments and related objects to database."""
        skipped = 0
        for payment in payments:
            try:
                skipped += self._save_if_not_exists(payment)
            except ValidationError as error:
                skipped += 1
                message = 'Payment ID %s has not been saved due to the following errors:'
                LOGGER.warning(message, payment.identifier)
                if self.options['verbosity'] >= 1:
                    self.stderr.write(self.style.WARNING(message % payment.identifier))

                if hasattr(error, 'message_dict'):
                    for field in error.message_dict:
                        prefix = '{}: '.format(field) if field != '__all__' else ''
                        for message in error.message_dict[field]:
                            LOGGER.warning('%s%s', prefix, message)
                            if self.options['verbosity'] >= 1:
                                self.stderr.write(self.style.WARNING('%s%s' % (prefix, message)))
                else:
                    LOGGER.warning('\n'.join(error.messages))
                    if self.options['verbosity'] >= 1:
                        self.stderr.write(self.style.WARNING('\n'.join(error.messages)))
            except IntegrityError as error:
                skipped += 1
                message = 'Payment ID %s has not been saved due to the following error: %s'
                LOGGER.warning(message, payment.identifier, str(error))
                if self.options['verbosity'] >= 1:
                    self.stderr.write(self.style.WARNING(message % (payment.identifier, str(error))))
            else:
                if self.options['verbosity'] >= 2:
                    self.stdout.write(self.style.SUCCESS('Payment ID {} has been imported.'.format(payment.identifier)))
        if skipped:
            LOGGER.info('Skipped %d payments.', skipped)

    def _save_if_not_exists(self, payment: BankPayment) -> int:
        """Return value is the number of skipped payments."""
        with transaction.atomic():
            if self._payment_exists(payment):
                LOGGER.info('Payment ID %s already exists - skipping.', payment)
                return 1
            else:
                payment.full_clean()
                for callback in SETTINGS.import_callbacks:
                    payment = callback(payment)
                payment.save()
                return 0

    def _payment_exists(self, payment: BankPayment) -> bool:
        query = BankPayment.objects.filter(account=payment.account, identifier=payment.identifier)
        return query.exists()
