from django.conf import settings
from django.conf.urls.defaults import *

urlpatterns = patterns('vith_core.views',
    url('^tracks/$', 'tracks'),
    url('^now_playing/$', 'now_playing'),
    url('^upload/$', 'upload'),    
    url('^vote/$', 'vote')
)
