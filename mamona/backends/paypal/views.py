from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.views.generic.simple import direct_to_template
from django.contrib.sites.models import Site

from mamona.models import Payment
from mamona.utils import get_backend_settings

import urllib2
from urllib import urlencode

def confirm(request, payment_id):
	payment = get_object_or_404(Payment, id=payment_id, status='in_progress', backend='paypal')
	paypal = get_backend_settings('paypal')
	try:
		return_url = paypal['return_url']
	except KeyError:
		# TODO: use https when needed
		return_url = 'http://%s%s' % (
				Site.objects.get_current().domain,
				reverse('mamona-paypal-return', kwargs={'payment_id': payment.id})
				)
	notify_url = 'http://%s%s' % (
			Site.objects.get_current().domain,
			reverse('mamona-paypal-ipn')
			)
	items = payment.get_items()
	customer = payment.get_customer_data()
	return direct_to_template(
			request,
			'mamona/backends/paypal/confirm.html',
			{
				'payment': payment, 'items': items, 'customer': customer,
				'paypal': paypal,
				'return_url': return_url, 'notify_url': notify_url
				}
			)

def return_from_gw(request, payment_id):
	payment = get_object_or_404(Payment, id=payment_id)
	return direct_to_template(
			request,
			'mamona/backends/paypal/return.html',
			{'payment': payment}
			)

def ipn(request):
	"""Instant Payment Notification callback.
	See https://cms.paypal.com/us/cgi-bin/?&cmd=_render-content&content_ID=developer/e_howto_admin_IPNIntro
	for details."""
	# TODO: add some logging here, as all the errors will occur silently
	payment = get_object_or_404(Payment, id=request.POST['invoice'], status='in_progress', backend='paypal')
#	print "%s: %s" % (payment.id, payment)
	data = list(request.POST.items())
	data.insert(0, ('cmd', '_notify-validate'))
	udata = urlencode(data)
	url = get_backend_settings('paypal')['url']
#	print url
	r = urllib2.Request(url)
	r.add_header("Content-type", "application/x-www-form-urlencoded")
	h = urllib2.urlopen(r, udata)
	result = h.read()
#	print h.code
#	print repr(result)
	h.close()

	if result == "VERIFIED":
#		print "verified"
		# TODO: save foreign-id from data['txn_id']
		payment.on_success()
		return HttpResponse('OKTHXBAI')
	else:
#		print "not verified"
		# XXX: marking the payment as failed would create a security hole
		return HttpResponseNotFound()