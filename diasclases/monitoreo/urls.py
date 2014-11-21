from django.conf.urls import patterns, url

urlpatterns=patterns('diasclases.monitoreo.views', 
		url(r'^reportar-semana/$', 'view_reportar_semana', name='vista_reportar_semana'),
		url(r'^generar-semana-ajax/(?P<centro_voluntario_id>\d+)/(?P<semana_id>\d+)/$', 'view_semana_ajax', name='vista_semana_ajax'),
		url(r'^reportar-semana-centro/(?P<centro_voluntario_id>\d+)/$', 'view_reportar_semana_centrovoluntario', name='vista_reportar_semana_centrovoluntario'),
		url(r'^eliminar-semana-centro/(?P<centro_voluntario_id>\d+)/(?P<semana_id>\d+)/$', 'view_eliminar_semana', name='vista_eliminar_semana'),
		url(r'^inicio-reportes/$', 'view_inicio_reportes', name='vista_inicio_reportes'),
		url(r'^inicio-reportes-nacional/$', 'view_reporte_nacional', name='vista_reporte_nacional'),
		url(r'^inicio-reportes-municipal/$', 'view_reporte_municipal', name='vista_reporte_municipal'),
		url(r'^inicio-reportes-totalvoluntarios/$', 'view_reporte_totalvoluntarios', name='vista_reporte_totalvoluntarios'),
)