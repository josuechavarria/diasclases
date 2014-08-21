from django.conf.urls import patterns, url

urlpatterns=patterns('diasclases.general.views', 
		url(r'^$', 'view_login', name='vista_principal'),
		url(r'^inicio/$', 'view_index', name='vista_inicio'),
		url(r'^accounts/login/$', 'view_logout', name='vista_login'),
		url(r'^accounts/logout/$', 'view_logout', name='vista_logout'),
		url(r'^nueva-persona/$', 'view_nueva_persona', name='vista_nueva_persona'),
		url(r'^administration/people/ajaxmuni/$', 'view_people_ajax_municipio', name='vista_ajax_municipio'),
		url(r'^data-centro-ajax/$', 'view_centro_ajax', name='vista_centro_ajax'),
		url(r'^generar-excel/$', 'view_generar_excel', name='vista_generar_excel'),
		url(r'^leer-excel/$', 'view_leer_excel', name='vista_leer_excel'),
		url(r'^consultar-data/$', 'view_consultar_centros', name='vista_consultar_centros'),
		url(r'^consultar-semanas-centro/(?P<centro_voluntario_id>\d+)/$', 'view_consultar_semanas', name='vista_consultar_semanas'),
		url(r'^consultar-data-voluntarios/$', 'view_consultar_voluntarios', name='vista_consultar_voluntarios')
)