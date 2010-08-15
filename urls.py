from django.conf import settings
from django.conf.urls.defaults import *

from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns('',
    (r'^(?P<path>.*\.(js|css|xls|ico|png|gif|jpg|txt|doc|xpi|rdf|exe|swf|msi|crx|xml|mp3|jar|cab|tar))$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),

    (r'^admin/', include(admin.site.urls)),
    (r'^', include('vith_core.urls')),
    
    url('^$', 'django.views.generic.simple.direct_to_template', {'template': 'base.html'}),
)
