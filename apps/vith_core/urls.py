from django.conf import settings
from django.conf.urls.defaults import *

urlpatterns = patterns('vith_core.views',
    url('^tracks/$', 'tracks'),
    url('^upload/$', 'upload'),
)
