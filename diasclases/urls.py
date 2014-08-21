from django.conf.urls import patterns, include, url
import settings
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'diasclases.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^', include('diasclases.general.urls')),
    url(r'^monitoreo/', include('diasclases.monitoreo.urls')),
    url(r'^medios/(?P<path>.*)$', 'django.views.static.serve', {'document_root':settings.MEDIA_ROOT}) #permite el acceso a carpeta media
)
