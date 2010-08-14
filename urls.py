from django.conf import settings
from django.conf.urls.defaults import *

from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns('',
    (r'^(?P<path>.*\.(js|gm4ie|css|xls|ico|png|gif|jpg|doc|xpi|rdf|exe|msi|crx|xml))$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),

    (r'^admin/', include(admin.site.urls)),
    (r'^', include('vith_core.urls')),
    
    url('^$', 'django.views.generic.simple.direct_to_template', {'template': 'base.html'}),
)
