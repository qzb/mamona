from django.conf import settings
import sys

def get_active_backends():
	try:
		return settings.MAMONA_ACTIVE_BACKENDS
	except AttributeError:
		return ()

def import_backend_modules(submodule=''):
	try:
		backends = settings.MAMONA_ACTIVE_BACKENDS
	except AttributeError:
		backends = []
	modules = {}
	for backend_name in backends:
		path = backend_name
		if submodule:
			path = '%s.%s' % (path, submodule)
		try:
			__import__(path)
		except ImportError:
			#TODO: add deprecation warning
			path = 'mamona.backends.%s' % path
			__import__(path)
		modules[backend_name] = sys.modules[path]
	return modules

def get_backend_choices():
	choices = []
	backends = import_backend_modules()
	for name, module in backends.items():
		choices.append((name, module.BACKEND_NAME))
	return choices

def get_backend_settings(backend):
	try:
		return settings.MAMONA_BACKENDS_SETTINGS[backend]
	except (AttributeError, KeyError):
		return {}


