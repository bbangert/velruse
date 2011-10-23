"""Facebook Authentication Views

"""
from urlparse import parse_qs

from pyramid.httpexceptions import HTTPFound
from simplejson import loads
import requests

from velruse.exceptions import AuthenticationComplete
from velruse.exceptions import AuthenticationDenied
from velruse.exceptions import CSRFError
from velruse.exceptions import ThirdPartyFailure
from velruse.parsers import extract_fb_data
from velruse.utils import flat_url

def facebook_login(request):
	"""Initiate a facebook login"""
	config = request.registry['velruse_config']
	if config.get('accept_form_scope'):
		scope = request.POST.get('scope')
	else:
		scope = config.get('facebook_scope', '')
	request.session['state'] = state = uuid.uuid4().hex
	fb_url = flat_url('https://www.facebook.com/dialog/oauth/', scope=scope,
					  client_id=config['facebook_app_id'],
					  redirect_uri=request.route_url('facebook_process'),
					  state=state)
	return HTTPFound(location=fb_url)


def facebook_process(request):
	"""Process the facebook redirect"""
	if request.GET.get('state') != request.session['state']:
		raise CSRFError
	config = request.registry['velruse_config']
	code = request.GET.get('code')
	if not code:
		reason = request.GET.get('error_reason', 'No reason provided.')
		raise AuthenticationDenied(reason)

	# Now retrieve the access token with the code
	access_url = flat_url('https://graph.facebook.com/oauth/access_token',
						  client_id=config['facebook_app_id'], code=code,
						  client_secret=config['facebook_app_secret'],
						  redirect_uri=request.route_url('facebook_process'))
	r = requests.get(access_url)
	if r.status_code != 200:
		raise ThirdPartyFailure("Status %s: %s" % (r.status_code, r.content))
	access_token = parse_qs(r.content)['access_token'][0]

	# Retrieve profile data
	graph_url = flat_url('https://graph.facebook.com/me',
						 access_token=access_token)
	r = requests.get(graph_url)
	if r.status_code != 200:
		raise ThirdPartyFailure("Status %s: %s" % (r.status_code, r.content))
	fb_profile = loads(r.content)
	profile = extract_fb_data(fb_profile)

	# Create and raise our AuthenticationComplete exception with the
	# appropriate data to be passed
	complete = AuthenticationComplete()
	complete.profile = profile
	complete.access_token = access_token
	complete.providor = 'Facebook'
	raise complete
