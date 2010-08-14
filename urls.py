from django.conf import settings
from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    (r'^(?P<path>.*\.(js|gm4ie|css|xls|ico|png|gif|jpg|doc|xpi|rdf|exe|msi|crx|xml))$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),

    # Example:
    # (r'^voices_in_the_head/', include('voices_in_the_head.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),

    url('^$', 'django.views.generic.simple.direct_to_template', {'template': 'base.html'})
)
