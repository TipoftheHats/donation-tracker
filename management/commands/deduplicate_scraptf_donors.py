from structlog import get_logger

from tracker.models import Donor, Donation
import tracker.commandutil as commandutil
import tracker.viewutil as viewutil

log = get_logger()


# Because Justin was lazy^H^H^H^Hbusy, the import_item_donations command didn't
# do the work of checking if a Donor with the email address in the item
# donation already existed. Every ScrapTF donation imported got its very own
# Donor. These need to be deduplicated for many reasons, including prizes.
#
# Some assumptions are made:
# * one donor = one donation
class Command(commandutil.TrackerCommand):
    help = 'Merge ScrapTF donors into existing PayPal donors'

    def add_arguments(self, parser):
        parser.add_argument('-e', '--event', required=True,
                            help='specify which tracker event to deduplicate ScrapTF donors in',
                            type=viewutil.get_event)
        parser.add_argument('--report',
                            action='store_true',
                            help="report likely potential changes, but don't do anything")
        parser.add_argument('--actually-do-the-thing',
                            action='store_true',
                            help='confirm that you would like donors to be merged')

    def handle(self, *args, **options):
        super(Command, self).handle(*args, **options)
        event = options['event']

        scraptf_donations = Donation.objects.filter(
            domain='SCRAPTF',
            event=event)

        log.info('ScrapTF donations ready.',
                 tracker_event=event,
                 num=len(scraptf_donations))

        if options['report']:
            self.report(scraptf_donations)
            return

        if not options['actually_do_the_thing']:
            print 'Action not confirmed. Set --actually-do-the-thing. Exiting.'
            return

        for donation in scraptf_donations.iterator():
            root = self.find_root_donor(donation)
            if root:
                dupe = donation.donor
                log.info('Merging donors.',
                         dupe="#{}: {} {}".format(dupe.id, dupe.email, repr(dupe)),
                         root="#{}: {} {}".format(root.id, root.email, repr(root)),
                         )
                viewutil.merge_donors(root, [dupe])

    def report(self, scraptf_donations):
        results = []
        for donation in scraptf_donations.iterator():
            root = self.find_root_donor(donation)
            if root:
                results.append((donation.donor, root))

        log.info('Root donors ready.', num=len(results))
        print results
        print 'Report finished.'


    def find_root_donor(self, donation):
        """
        Attempt to find a root donor for the given Donation.

        If no appropriate root donor is found, returns None. (The donation's
        existing donor is the root donor.)
        """

        # ll = log.bind(donation_id=donation.id,
        #               donation_steamid=donation.steamid,
        #               donor_id=donation.donor.id,
        #               donor_email=donation.donor.email)

        # Be sure to exclude THIS donation's donor and use the same event.
        notme = Donor.objects.exclude(id=donation.donor.id)

        # Find a donor that has the same email and has made a paypal donation.
        d = notme.filter(
            email=donation.donor.email,
            paypalemail__isnull=False
        ).exclude(paypalemail='').order_by('-id').first()
        if d:
            return d

        # Find the earliest ScrapTF donor with the same email.
        d = notme.filter(
            email=donation.donor.email,
            donation__domain='SCRAPTF',
        ).order_by('id').first()
        if d:
            return d

        # Find the earliest ScrapTF donor with a donation having the same
        # steamid.
        d = notme.filter(
            donation__domain='SCRAPTF',
            donation__steamid=donation.steamid,
        ).order_by('id').first()
        if d:
            return d

        return None
