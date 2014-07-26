from django.db import models
from django.db.models import signals
from django.core.exceptions import ValidationError
from django.dispatch import receiver

from tracker.validators import *
from event import Event

from decimal import Decimal
import pytz
import datetime
import cld

__all__ = [
  'Donation',
  'Donor',
]

_currencyChoices = (('USD','US Dollars'),('CAD', 'Canadian Dollars'))

DonorVisibilityChoices = (('FULL', 'Fully Visible'), ('FIRST', 'First Name, Last Initial'), ('ALIAS', 'Alias Only'), ('ANON', 'Anonymous'))

DonationDomainChoices = (('LOCAL', 'Local'), ('CHIPIN', 'ChipIn'), ('PAYPAL', 'PayPal'))

LanguageChoices = (('un', 'Unknown'), ('en', 'English'), ('fr', 'French'), ('de', 'German'))

def LatestEvent():
  try:
    return Event.objects.latest()
  except Event.DoesNotExist:
    return None

class DonationManager(models.Manager):
  def get_by_natural_key(self, domainId):
    return self.get(domainId=domainId)

class Donation(models.Model):
  objects = DonationManager()
  donor = models.ForeignKey('Donor', blank=True, null=True)
  event = models.ForeignKey('Event', default=LatestEvent)
  domain = models.CharField(max_length=255,default='LOCAL',choices=DonationDomainChoices)
  domainId = models.CharField(max_length=160,unique=True,editable=False,blank=True)
  transactionstate = models.CharField(max_length=64, default='PENDING', choices=(('PENDING', 'Pending'), ('COMPLETED', 'Completed'), ('CANCELLED', 'Cancelled'), ('FLAGGED', 'Flagged')),verbose_name='Transaction State')
  bidstate = models.CharField(max_length=255,default='PENDING',choices=(('PENDING', 'Pending'), ('IGNORED', 'Ignored'), ('PROCESSED', 'Processed'), ('FLAGGED', 'Flagged')),verbose_name='Bid State')
  readstate = models.CharField(max_length=255,default='PENDING',choices=(('PENDING', 'Pending'), ('READY', 'Ready to Read'), ('IGNORED', 'Ignored'), ('READ', 'Read'), ('FLAGGED', 'Flagged')),verbose_name='Read State')
  commentstate = models.CharField(max_length=255,default='ABSENT',choices=(('ABSENT', 'Absent'), ('PENDING', 'Pending'), ('DENIED', 'Denied'), ('APPROVED', 'Approved'), ('FLAGGED', 'Flagged')),verbose_name='Comment State')
  amount = models.DecimalField(decimal_places=2,max_digits=20,validators=[positive,nonzero],verbose_name='Donation Amount')
  fee = models.DecimalField(decimal_places=2,max_digits=20,default=Decimal('0.00'),validators=[positive],verbose_name='Donation Fee')
  currency = models.CharField(max_length=8,null=False,blank=False,choices=_currencyChoices,verbose_name='Currency')
  timereceived = models.DateTimeField(default=datetime.datetime.now,verbose_name='Time Received')
  comment = models.TextField(blank=True,verbose_name='Comment')
  modcomment = models.TextField(blank=True,verbose_name='Moderator Comment')
  # Specifies if this donation is a 'test' donation, i.e. generated by a sandbox test, and should not be counted
  testdonation = models.BooleanField(default=False)
  requestedvisibility = models.CharField(max_length=32, null=False, blank=False, default='CURR', choices=(('CURR', 'Use Existing (Anonymous if not set)'),) + DonorVisibilityChoices, verbose_name='Requested Visibility')
  requestedalias = models.CharField(max_length=32, null=True, blank=True, verbose_name='Requested Alias')
  requestedemail = models.EmailField(max_length=128, null=True, blank=True, verbose_name='Requested Contact Email')
  commentlanguage = models.CharField(max_length=32, null=False, blank=False, default='un', choices=LanguageChoices, verbose_name='Comment Language')
  class Meta:
    app_label = 'tracker'
    permissions = (
      ('delete_all_donations', 'Can delete non-local donations'),
      ('view_full_list', 'Can view full donation list'),
      ('view_comments', 'Can view all comments'),
      ('view_pending', 'Can view pending donations'),
      ('view_test', 'Can view test donations'),
    )
    get_latest_by = 'timereceived'
    ordering = [ '-timereceived' ]

  def bid_total(self):
    return reduce(lambda a, b: a + b, map(lambda b: b.amount, self.bids.all()), Decimal('0.00'))

  def clean(self,bid=None):
    super(Donation,self).clean()
    if not self.donor and self.transactionstate != 'PENDING':
      raise ValidationError('Donation must have a donor when in a non-pending state')
    if not self.domainId and self.donor:
      self.domainId = str(calendar.timegm(self.timereceived.timetuple())) + self.donor.email
    bids = set()
    if bid:
      bids |= set([bid])
    bids |= set()|set(self.bids.all())
    bids = map(lambda b: b.amount,bids)
    bidtotal = reduce(lambda a,b: a+b,bids,Decimal('0'))
    if self.amount and bidtotal > self.amount:
      raise ValidationError('Bid total is greater than donation amount: %s > %s' % (bidtotal,self.amount))

    tickets = self.tickets.all()
    print(tickets)
    ticketTotal = reduce(lambda a,b: a+b, map(lambda b: b.amount, tickets), Decimal('0'))
    if self.amount and ticketTotal > self.amount:
      raise ValidationError('Prize ticket total is greater than donation amount: %s > %s' % (ticketTotal,self.amount))

    if self.comment:
      if self.commentlanguage == 'un' or self.commentlanguage == None:
        detectedLangName, detectedLangCode, isReliable, textBytesFound, details = cld.detect(self.comment.encode('utf-8'), hintLanguageCode ='en')
        if detectedLangCode in map(lambda x: x[0], LanguageChoices):
          self.commentlanguage = detectedLangCode
        else:
          self.commentlanguage = 'un'
    else:
      self.commentlanguage = 'un'
    if self.domain == 'LOCAL': # local donations are always complete, duh
      self.transacationstate = 'COMPLETED'
  def __unicode__(self):
    return unicode(self.donor) + ' (' + unicode(self.amount) + ') (' + unicode(self.timereceived) + ')'

@receiver(signals.post_save, sender=Donation)
def DonationBidsUpdate(sender, instance, created, raw, **kwargs):
  if raw: return
  if instance.transactionstate == 'COMPLETED':
    for b in instance.bids.all():
      b.save()

class DonorManager(models.Manager):
  def get_by_natural_key(self, email):
    return self.get(email=email)

class Donor(models.Model):
  objects = DonorManager()
  email = models.EmailField(max_length=128,unique=True,verbose_name='Contact Email')
  alias = models.CharField(max_length=32,unique=True,null=True,blank=True)
  firstname = models.CharField(max_length=64,blank=True,verbose_name='First Name')
  lastname = models.CharField(max_length=64,blank=True,verbose_name='Last Name')
  visibility = models.CharField(max_length=32, null=False, blank=False, default='FIRST', choices=DonorVisibilityChoices)

  # Address information, yay!
  addresscity = models.CharField(max_length=128,blank=True,null=False,verbose_name='City')
  addressstreet = models.CharField(max_length=128,blank=True,null=False,verbose_name='Street/P.O. Box')
  addressstate = models.CharField(max_length=128,blank=True,null=False,verbose_name='State/Province')
  addresszip = models.CharField(max_length=128,blank=True,null=False,verbose_name='Zip/Postal Code')
  addresscountry = models.CharField(max_length=128,blank=True,null=False,verbose_name='Country')

  # Donor specific info
  paypalemail = models.EmailField(max_length=128,unique=True,null=True,blank=True,verbose_name='Paypal Email')

  # Runner info
  runneryoutube = models.CharField(max_length=128,unique=True,blank=True,null=True,verbose_name='Youtube Account')
  runnertwitch = models.CharField(max_length=128,unique=True,blank=True,null=True,verbose_name='Twitch Account')
  runnertwitter = models.CharField(max_length=128,unique=True,blank=True,null=True,verbose_name='Twitter Account')

  # Prize contributor info
  prizecontributoremail = models.EmailField(max_length=128,unique=True,blank=True,null=True,verbose_name='Contact Email')
  prizecontributorwebsite = models.URLField(blank=True,null=True,verbose_name='Personal Website')

  class Meta:
    app_label = 'tracker'
    permissions = (
      ('delete_all_donors', 'Can delete donors with cleared donations'),
      ('view_usernames', 'Can view full usernames'),
      ('view_emails', 'Can view email addresses'),
    )
    ordering = ['lastname', 'firstname', 'email']
  def clean(self):
    # an empty value means a null value
    if not self.alias:
      self.alias = None
    if not self.paypalemail:
      self.paypalemail = None
    if self.visibility == 'ALIAS' and not self.alias:
      raise ValidationError("Cannot set Donor visibility to 'Alias Only' without an alias")
    if not self.runneryoutube:
      self.runneryoutube = None
    if not self.runnertwitch:
      self.runnertwitch = None
    if not self.runnertwitter:
      self.runnertwitter = None
    if not self.prizecontributoremail:
      self.prizecontributoremail = None
    if not self.prizecontributorwebsite:
      self.prizecontributorwebsite = None
  def visible_name(self):
    if self.visibility == 'ANON':
      return u'(Anonymous)'
    elif self.visibility == 'ALIAS':
      return self.alias
    last_name,first_name = self.lastname,self.firstname
    if not last_name and not first_name:
      return u'(No Name)' if self.alias == None else self.alias
    if self.visibility == 'FIRST':
      last_name = last_name[:1] + u'...'
    return last_name + u', ' + first_name + (u'' if self.alias == None else u' (' + self.alias + u')')
  def full(self):
    return unicode(self.email) + u' (' + unicode(self) + u')'
  def __unicode__(self):
    if not self.lastname and not self.firstname:
      return self.alias or u'(No Name)'
    ret = unicode(self.lastname) + ', ' + unicode(self.firstname)
    if self.alias:
      ret += u' (' + unicode(self.alias) + u')'
    return ret

