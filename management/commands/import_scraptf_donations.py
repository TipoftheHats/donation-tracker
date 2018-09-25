from datetime import datetime
from decimal import Decimal
import pytz
import traceback

from django.conf import settings
from django.core.management.base import CommandError
from django.db import IntegrityError, transaction
from structlog import get_logger

from tracker.models import Donation, DonationBid, BidSuggestion
from tracker.scraptf import ScrapTF
import tracker.commandutil as commandutil
import tracker.viewutil as viewutil

log = get_logger()


class Command(commandutil.TrackerCommand):
    help = 'Import item donations from Scrap.TF'

    def add_arguments(self, parser):
        parser.add_argument('-f', '--fundraiser', required=True,
                            help='the name of the Scrap.TF fundraiser')
        parser.add_argument('-e', '--event', required=True,
                            help='specify the tracker event to import donations to',
                            type=viewutil.get_event)

    def handle(self, *args, **options):
        super(Command, self).handle(*args, **options)

        latest_donation = self.get_latest_scraptf_donation()
        after = latest_donation.timereceived if latest_donation else None

        key = getattr(settings, 'SCRAPTF_API_KEY')
        if not key:
            raise CommandError('A Scrap.TF api key is required.')
        fundraiser = options['fundraiser']

        try:
            donations = ScrapTF(key).get_latest_donations(fundraiser, after)
        except Exception as e:
            log.critical('Failed to get latest donations from Scrap.TF.',
                         exception=repr(e))
            raise CommandError(e)

        failed = 0
        for donation in donations:
            try:
                self.commit_scraptf_donation(donation)
            except Exception as e:
                log.error('Failed to commit ScrapTF donation.',
                          exception=repr(e),
                          donation_id=donation['id'])
                traceback.print_exc()
                failed += 1

        log.info('All done!',
                 failed=failed,
                 total=len(donations))

    def get_latest_scraptf_donation(self):
        return Donation.objects.filter(domain__exact='SCRAPTF').order_by('-timereceived').first()

    @transaction.atomic
    def commit_scraptf_donation(self, donation):
        """
        From a ScrapTF donation, create a Donation. If incentives are
        present, create all DonationBids and BidSuggestions as well.
        """

        # First, gather all Donation fields
        domain_id = donation['id']
        amount = Decimal(donation['cash_value'])
        time = datetime.fromtimestamp(donation['confirmed_time'], tz=pytz.utc)
        comment = donation.get('message', '')
        commentstate = 'PENDING' if len(comment) > 0 else 'ABSENT'

        user = donation.get('user', {})
        alias = user.get('name')
        steamid = user.get('steamid')
        email = donation.get('email')

        d = Donation(domain='SCRAPTF',
                     domainId=domain_id,
                     transactionstate='COMPLETED',
                     amount=amount,
                     timereceived=time,
                     comment=comment,
                     commentstate=commentstate,
                     requestedalias=alias,
                     requestedemail=email,
                     steamid=steamid)

        try:
            d.save()
        except IntegrityError:
            log.debug('Donation already exists, refusing to modify it.',
                      donation_id=domain_id)
            return

        # Only proceed if incentives are present
        incentives = donation.get('incentives')
        if not incentives:
            return
        log.info("Donation has incentives, creating them now.",
                 incentives_total=len(incentives))

        # Ensure the incentives don't exceed the total donation amount
        inc_amounts = [Decimal(inc['amount']) for inc in incentives]
        inc_total = sum(inc_amounts)
        if inc_total > amount:
            raise Exception("sum of incentive amounts exceeds donation amount")

        for inc in incentives:
            # First grab the bid to make sure it exists
            bid = Bid.objects.get(pk=inc['incentive'])

            dbid = DonationBid(donation=d,
                              bid=bid,
                              amount=Decimal(inc['amount']))
            dbid.save()

            # If the incentive has a custom value, create a BidSuggestion
            suggestion = inc.get('custom')
            if suggestion:
                s = BidSuggestion(bid=bid,
                                  name=suggestion)
                s.save()
