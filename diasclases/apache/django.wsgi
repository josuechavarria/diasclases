import os, sys
sys.path.append('/var/www/')
sys.path.append('/var/www/diasclases')

os.environ['DJANGO_SETTINGS_MODULE'] = 'diasclases.settings'

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()