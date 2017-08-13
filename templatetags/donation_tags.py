from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django.db.models import Q

import datetime
import locale
import urllib

import tracker.viewutil as viewutil

register = template.Library()

def tryresolve(var, context, default=None):
  try:
    return var.resolve(context)
  except template.VariableDoesNotExist:
    return default

def sortlink(style, contents, **args):
  args = filter(lambda i: i[1], args.items())
  ret = []
  ret.append('<a href="?')
  ret.append(conditional_escape(urllib.urlencode(args)))
  ret.append('"')
  if style: ret.append(' class="%s"' % style)
  ret.append('>')
  if style: ret.append('<span style="display:none;">')
  ret.append(contents)
  if style: ret.append('</span>')
  ret.append('</a>')
  return ''.join(map(unicode,ret))

@register.simple_tag(takes_context=True)
def sort(context, sort_field, page=1):
  return sortlink('asc', 'Asc', sort=sort_field, order=1, page=page) + sortlink('dsc', 'Dsc', sort=sort_field, order=-1, page=page)

@register.tag("pagefirst")
@register.tag("pagefull")
def do_pageff(parser, token):
  try:
    tag_name, = token.split_contents()
  except ValueError:
    raise template.TemplateSyntaxError('%r tag takes no arguments' % token.contents.split()[0])
  return PageFLFNode(tag_name)

@register.tag("pagelast")
def do_pagel(parser, token):
  try:
    tag_name, page = token.split_contents()
  except ValueError:
    raise template.TemplateSyntaxError('%r tag takes one argument' % token.contents.split()[0])
  return PageFLFNode(tag_name, page)

class PageFLFNode(template.Node):
  def __init__(self, tag, page='request.GET.page'):
    self.tag = tag
    self.page = template.Variable(page)
  def render(self, context):
    sort = tryresolve(template.Variable('request.GET.sort'),context)
    order = tryresolve(template.Variable('request.GET.order'),context)
    if self.tag == 'pagefirst':
      return sortlink('first', '|&lt; ', sort=sort, order=order, page=1)
    elif self.tag == 'pagelast':
      page = self.page.resolve(context)
      return sortlink('last', '&gt;| ', sort=sort, order=order, page=page)
    elif self.tag == 'pagefull':
      return sortlink(None, 'View Full List', sort=sort, order=order, page='full')

@register.tag("pageprev")
@register.tag("pagenext")
def do_pagepn(parser, token):
  try:
    tag_name, page = token.split_contents()
  except ValueError:
    raise template.TemplateSyntaxError('%r tag requires one argument' % token.contents.split()[0])
  return PagePNNode(tag_name, page)

class PagePNNode(template.Node):
  dc = { 'pageprev' : '< ', 'pagenext' : '> ' }
  def __init__(self, tag, page):
    self.tag = tag
    self.page = template.Variable(page)
  def render(self, context):
    sort = tryresolve(template.Variable('request.GET.sort'),context)
    order = tryresolve(template.Variable('request.GET.order'),context)
    page = self.page.resolve(context)
    return sortlink(self.tag[4:], PagePNNode.dc[self.tag], sort=sort, order=order, page=page)

@register.tag("pagelink")
def do_pagelink(parser, token):
  try:
    tag_name, page = token.split_contents()
  except ValueError:
    raise template.TemplateSyntaxError('%r tag requires one argument' % token.contents.split()[0])
  return PageLinkNode(tag_name, page)

class PageLinkNode(template.Node):
  def __init__(self, tag, page):
    self.tag = tag
    self.page = template.Variable(page)
  def render(self, context):
    sort = tryresolve(template.Variable('request.GET.sort'),context)
    order = tryresolve(template.Variable('request.GET.order'),context)
    page = self.page.resolve(context)
    return sortlink('', page, sort=sort, order=order, page=page)

@register.tag("datetime")
def do_datetime(parser, token):
  try:
    tag_name, date = token.split_contents()
  except ValueError:
    raise template.TemplateSyntaxError('%r tag requires one argument' % token.contents.split()[0])
  return DateTimeNode(tag_name, date)

class DateTimeNode(template.Node):
  def __init__(self, tag, date):
    self.tag = tag
    self.date = template.Variable(date)
  def render(self, context):
    date = self.date.resolve(context)
    return '<span class="datetime">' + date.strftime('%m/%d/%Y %H:%M:%S') + ' +0000</span>'

@register.tag("rendertime")
def do_rendertime(parser, token):
  try:
    tag_name, time = token.split_contents()
  except ValueError:
    raise template.TemplateSyntaxError('%r tag requires a single argument' % token.contents.split()[0])
  return RenderTimeNode(time)

class RenderTimeNode(template.Node):
  def __init__(self, time):
    self.time = template.Variable(time)
  def render(self, context):
    try:
      time = self.time.resolve(context)
      try:
        now = datetime.datetime.now() - time
      except TypeError:
        return ''
      return '%d.%d seconds' % (now.seconds,now.microseconds)
    except template.VariableDoesNotExist:
      return ''

@register.simple_tag(takes_context=True, name='bid')
def do_bid(bid):
  return '' # ???


@register.simple_tag(takes_context=True, name='donor_link')
def donor_link(context, donor, event=None):
  if donor.visibility != 'ANON':
    return '<a href="%s">%s</a>' % (donor.get_absolute_url(event), donor.visible_name())
  else:
    return donor.visible_name()


@register.filter
def forumfilter(value, autoescape=None):
  if autoescape:
    esc = conditional_escape
  else:
    esc = lambda x: x
  return mark_safe(esc(value).replace('\n', '<br />'))
forumfilter.is_safe = True
forumfilter.needs_autoescape = True

@register.filter
def money(value):
  locale.setlocale( locale.LC_ALL, '')
  try:
    if not value:
      return locale.currency(0.0)
    return locale.currency(value, symbol=True, grouping=True)
  except ValueError:
    locale.setlocale( locale.LC_MONETARY, ('en', 'us'))
    if not value:
      return locale.currency(0.0)
    return locale.currency(value, symbol=True, grouping=True)
money.is_safe = True

@register.filter("abs")
def filabs(value,arg):
  try:
    return abs(int(value)-int(arg))
  except ValueError:
    raise template.TemplateSyntaxError('abs requires integer arguments')

@register.filter("mod")
def filmod(value,arg):
  try:
    return int(value) % int(arg)
  except ValueError:
    raise template.TemplateSyntaxError('mod requires integer arguments')

@register.filter("negate")
def negate(value):
  return not value

# TODO: maybe store visibility option in UserProfile
@register.filter
def public_user_name(user):
    if user.donor:
        return user.donor.visible_name()
    elif user.username == user.email:
        return u'Anonymous'
    else:
        return user.username

@register.simple_tag
def admin_url(obj):
  return viewutil.admin_url(obj)

@register.simple_tag
def settings_value(name):
  return getattr(settings, name, None)

# This is a bit of a hack to be able to use settings in django
# html template conditional statements
@register.filter('find_setting')
def find_setting(name):
  return settings_value(name)

@register.simple_tag(takes_context=True)
def standardform(context, form, formid="formid", submittext='Submit', action=None, showrequired=True):
    return template.loader.render_to_string('standardform.html', template.Context({ 'form': form, 'formid': formid, 'submittext': submittext, action: action, 'csrf_token': context.get('csrf_token', None), 'showrequired': showrequired }))

@register.simple_tag(takes_context=True)
def form_innards(context, form, showrequired=True):
    return template.loader.render_to_string('form_innards.html', template.Context({ 'form': form, 'showrequired': showrequired, 'csrf_token': context.get('csrf_token', None)}))

@register.simple_tag
def address(donor):
    return template.loader.render_to_string('tracker/donor_address.html', template.Context({ 'donor': donor }))

@register.filter('mail_name')
def mail_name(donor):
    if donor.firstname or donor.lastname:
        return donor.firstname + ' ' + donor.lastname
    if donor.alias:
        return donor.alias
    return 'Occupant'

