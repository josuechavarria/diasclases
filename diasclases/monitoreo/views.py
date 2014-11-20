#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from django.shortcuts import render, render_to_response
from django.template import RequestContext
from django.contrib.auth.models import Group, User
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import permission_required, login_required
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.db.models import Q
from django.core import serializers
from django.db.models import Count, Sum, Avg
from diasclases.monitoreo.forms import *
from diasclases.general.models import *
from diasclases.monitoreo.models import *

import json, math, random
from datetime import datetime, timedelta
now = datetime.now()
from django.db import transaction, IntegrityError
from django.db import connections




@permission_required('monitoreo.puede_consultar_boletas', login_url='/inicio/')
@transaction.atomic
def view_reportar_semana(request):
	data=[]
	if request.user.is_superuser:
		centros_data=list(centro_educativo.objects.filter(pk__in=voluntario.objects.filter(centros__en_funcionamiento=True).values_list('centros__pk')).values_list('id','codigo','nombre', 'nivel'))
	else:
		filtro=persona.objects.filter(user=request.user.pk).values_list('departamentos_asignados__id')
		centros_data=list(centro_educativo.objects.filter(pk__in=voluntario.objects.filter(centros__en_funcionamiento=True).values_list('centros__pk'), departamento__pk__in=filtro).values_list('id','codigo','nombre', 'nivel'))
	#centros_data=list(centro_educativo.objects.filter(pk__in=voluntario.objects.filter(centros__anio=now.year, centros__en_funcionamiento=True).values_list('centros__pk')).values_list('id','codigo','nombre', 'nivel'))
	voluntarios_data=voluntario.objects.filter(centros__en_funcionamiento=True).values_list('centros__pk')
	
	jornadas=jornada.objects.all()
	print voluntarios_data
	print centros_data
	for centro in centros_data:
		data.append({
			'pk': centro[0],
			'codigo': centro[1],
			'nombre': centro[2],
			'nivel': centro[3]
		})
	#print data
	ctx={'data':data, 'jornada': jornadas}

	if request.method == 'POST':
		sid = transaction.savepoint()
		try:
			# obtener centro y actualizar tipo_docente
			centro=centro_educativo.objects.get(pk=request.POST.get('listacentros'))
			centro.tipo_docente=request.POST.get('tipo_docente')
			voluntarioP=voluntario.objects.get(identidad=request.POST.get('identidad'))
			# llenar tabla centro_voluntario con la jornada. Crear el registro solo si no existe
			if centro_voluntario.objects.filter(voluntario__pk=voluntarioP.pk,centro__pk=request.POST.get('listacentros'), jornada__pk=request.POST.get('jornada'), periodo=periodo.objects.get(activo=True).pk):
				print "hay centro voluntario"
				centrov=centro_voluntario.objects.get(voluntario__pk=voluntarioP.pk,centro__pk=request.POST.get('listacentros'), jornada__pk=request.POST.get('jornada'), periodo=periodo.objects.get(activo=True).pk)
				centro.save()
				transaction.savepoint_commit(sid)
				return HttpResponseRedirect(reverse('vista_reportar_semana_centrovoluntario', args=[centrov.pk]))

			else:
				print "no hay centro voluntario"
				if request.user.groups.get().name == 'SUPERVISOR' or request.user.groups.get().name == 'FACILITADOR' or request.user.groups.get().name == 'ADMINISTRADOR':
					periodos=periodo.objects.get(activo=True)
					jornadas2=jornada.objects.get(pk=request.POST.get('jornada'))
					insert_cv=centro_voluntario(
						periodo=periodos,
						centro=centro,
						voluntario=voluntarioP,
						jornada=jornadas2
					)
					centro.save()
					insert_cv.save()
					transaction.savepoint_commit(sid)
					return HttpResponseRedirect(reverse('vista_reportar_semana_centrovoluntario', args=[insert_cv.pk]))
				else:
					transaction.savepoint_rollback(sid)
					mensaje = '<br/>El centro educativo no ha registrado datos en esta jornada.'
					ctx = {'error':'cx', 'errores': mensaje, 'data':data, 'jornada': jornadas}
					return render_to_response('monitoreo/reportar-semana.html',ctx, context_instance=RequestContext(request))
				 #redirecciona a la raiz
			
		except IntegrityError, e:
			print e
			transaction.savepoint_rollback(sid)
			mensaje = 'Uno de los centros seleccionados ya tiene un voluntario asignado.'
			ctx = {'error':'cx', 'errores': mensaje, 'data':data, 'jornada': jornadas}
			return render_to_response('monitoreo/reportar-semana.html',ctx, context_instance=RequestContext(request))
		except Exception, e:
			print e
			transaction.savepoint_rollback(sid)
			mensaje = 'Ocurrió un error al guardar los datos por favor verifique la información digitada.'
			ctx = {'error':'cx', 'errores': mensaje, 'data':data, 'jornada': jornadas}
			return render_to_response('monitoreo/reportar-semana.html',ctx, context_instance=RequestContext(request))

	return render_to_response('monitoreo/reportar-semana.html',ctx, context_instance=RequestContext(request))

@permission_required('monitoreo.puede_consultar_boletas', login_url='/inicio/')
@transaction.atomic
def view_reportar_semana_centrovoluntario(request, centro_voluntario_id):
	centrov=centro_voluntario.objects.get(pk=centro_voluntario_id)

	# armar la semana con los lunes de cada semana en un select en plantilla
	# Trae las semanas que no se han reportado del centro
	calendario=calendario_academico.objects.exclude(pk__in=centro_semana.objects.filter(centro__periodo__pk=centrov.periodo.pk , centro__centro__pk=centrov.centro.pk , centro__jornada__pk=centrov.jornada.pk).values_list('semana__pk')).filter(fecha_inicio__year=periodo.objects.get(activo=True).anio).order_by('numero_semana')
	calendario2=calendario_academico.objects.filter(pk__in=centro_semana.objects.filter(centro__periodo__pk=centrov.periodo.pk , centro__centro__pk=centrov.centro.pk , centro__jornada__pk=centrov.jornada.pk).values_list('semana__pk')).filter(fecha_inicio__year=periodo.objects.get(activo=True).anio).order_by('numero_semana')
	ctx = {'centro_voluntario': centrov, 'calendario': calendario, 'reportadas': calendario2}
	return render_to_response('monitoreo/reportar-semana-centrovoluntario.html', ctx, context_instance=RequestContext(request))

@login_required
@transaction.atomic
def view_semana_ajax(request, centro_voluntario_id, semana_id):
	if request.method == 'GET':
		centrov=centro_voluntario.objects.get(pk=centro_voluntario_id)
		calendario2=calendario_academico.objects.exclude(pk__in=centro_semana.objects.filter(centro__periodo__pk=centrov.periodo.pk , centro__centro__pk=centrov.centro.pk , centro__jornada__pk=centrov.jornada.pk).values_list('semana__pk')).filter(fecha_inicio__year=periodo.objects.get(activo=True).anio).order_by('numero_semana')
		calendarioreportadas=calendario_academico.objects.filter(fecha_inicio__year=periodo.objects.get(activo=True).anio, pk__in=centro_semana.objects.filter(centro__periodo__pk=centrov.periodo.pk , centro__centro__pk=centrov.centro.pk , centro__jornada__pk=centrov.jornada.pk).values_list('semana__pk')).order_by('numero_semana')
		calendario=calendario_academico.objects.get(pk=semana_id)
		semana=[]
		for x in range(0,6):
			fecha=calendario.fecha_inicio+timedelta(days=x)
			if fecha.strftime("%A") != 'Sunday':
				semana.append({
					'id' : x,
					'dia':calendario.fecha_inicio+timedelta(days=x)
				})
			else:
				break
		print semana
		ctx = {'razones': razones.objects.all(), 'semana': semana, 'centro_voluntario': centrov, 'reportadas':calendarioreportadas, 'calendario':calendario2, 'calendario_id':semana_id}
		return render_to_response('monitoreo/reportar-semana-centrovoluntario.html', ctx, context_instance=RequestContext(request))
	elif request.method == 'POST':
		centrov=centro_voluntario.objects.get(pk=request.POST.get('centrovoluntario'))
		calendario=calendario_academico.objects.get(pk=request.POST.get('semana'))

		try:
			sid = transaction.savepoint()
			for x in range(0,6):
				if request.POST.get('fecha_'+str(x)) is not None:
					fecha=datetime.strptime(request.POST.get('fecha_'+str(x)), '%d/%m/%Y').date()
					if request.POST.get('dia_'+str(x)) == 'SI':
						huboclases=True
					elif request.POST.get('dia_'+str(x)) == 'NO':
						huboclases=False
					else:
						huboclases=True

					if request.POST.get('razon_'+str(x)) != '':
						id_razon=request.POST.get('razon_'+str(x))
					else:
						id_razon=0

					if razones.objects.filter(pk=id_razon):
						razon=razones.objects.get(pk=id_razon)
					else:
						razon=None

					print fecha, huboclases, razon
					
					insert=centro_semana(
						centro=centrov,
						semana=calendario,
						fecha=fecha,
						hubo_clases=huboclases,
						razon=razon,
						usuario_creador = User.objects.get(pk=request.user.pk),
						fecha_creacion = datetime.now(),
						usuario_modificador = User.objects.get(pk=request.user.pk),
						fecha_modificacion = datetime.now()
					)
					insert.save()

			transaction.savepoint_commit(sid)

			# Traer siguiente semana y redireccionar si no hay siempre mostrar pantalla
			calendario_next=list(calendario_academico.objects.exclude(pk__in=centro_semana.objects.filter(centro__periodo__pk=centrov.periodo.pk , centro__centro__pk=centrov.centro.pk , centro__jornada__pk=centrov.jornada.pk).values_list('semana__pk')).filter(fecha_inicio__year=periodo.objects.get(activo=True).anio).order_by('numero_semana')[:1])
			for ca in calendario_next:
				print ca.pk
				return HttpResponseRedirect(reverse('vista_semana_ajax', args=[centrov.pk, ca.pk]))
				break
			return HttpResponseRedirect(reverse('vista_reportar_semana_centrovoluntario', args=[centrov.pk]))


		except IntegrityError, e:
			print e
			transaction.savepoint_rollback(sid)
			calendario=calendario_academico.objects.exclude(pk__in=centro_semana.objects.filter(centro__periodo__pk=centrov.periodo.pk , centro__centro__pk=centrov.centro.pk , centro__jornada__pk=centrov.jornada.pk).values_list('semana__pk')).filter(fecha_inicio__year=periodo.objects.get(activo=True).anio).order_by('numero_semana')
			mensaje = 'Uno de los centros seleccionados ya tiene un voluntario asignado.'
			ctx = {'error':'cx', 'errores': mensaje, 'centro_voluntario': centrov, 'calendario': calendario}
			return render_to_response('monitoreo/reportar-semana-centrovoluntario.html',ctx, context_instance=RequestContext(request))
		except Exception, e:
			print e
			transaction.savepoint_rollback(sid)
			calendario=calendario_academico.objects.exclude(pk__in=centro_semana.objects.filter(centro__periodo__pk=centrov.periodo.pk , centro__centro__pk=centrov.centro.pk , centro__jornada__pk=centrov.jornada.pk).values_list('semana__pk')).filter(fecha_inicio__year=periodo.objects.get(activo=True).anio).order_by('numero_semana')
			mensaje = 'Ocurrió un error al guardar los datos por favor verifique la información digitada.'
			ctx = {'error':'cx', 'errores': mensaje, 'centro_voluntario': centrov, 'calendario': calendario}
			return render_to_response('monitoreo/reportar-semana-centrovoluntario.html',ctx, context_instance=RequestContext(request))

	else:
		return HttpResponse(0)

@permission_required('monitoreo.delete_centro_semana', login_url='/inicio/')
def view_eliminar_semana(request,centro_voluntario_id, semana_id=None):
	if semana_id:
		try:
			sid = transaction.savepoint()
			centrov=centro_voluntario.objects.get(pk=centro_voluntario_id)
			centro_semana.objects.filter(centro__periodo__pk=centrov.periodo.pk , centro__centro__pk=centrov.centro.pk , centro__jornada__pk=centrov.jornada.pk, semana=semana_id).delete()
			transaction.savepoint_commit(sid)
		except Exception, e:
			print e
			transaction.savepoint_rollback(sid)
			
		calendario_next=list(calendario_academico.objects.exclude(pk__in=centro_semana.objects.filter(centro__periodo__pk=centrov.periodo.pk , centro__centro__pk=centrov.centro.pk , centro__jornada__pk=centrov.jornada.pk).values_list('semana__pk')).filter(fecha_inicio__year=periodo.objects.get(activo=True).anio).order_by('numero_semana')[:1])
		for ca in calendario_next:
			print ca.pk
			return HttpResponseRedirect(reverse('vista_semana_ajax', args=[centro_voluntario_id, ca.pk]))
			break

def dictfetchall(cursor):
	"Returns all rows from a cursor as a dict"
	desc = cursor.description
	return [
		dict(zip([col[0] for col in desc], row))
		for row in cursor.fetchall()
	]


@permission_required('monitoreo.puede_entrar_reportes', login_url='/inicio/')
def view_inicio_reportes(request):
	ctx={}
	new_list=[]
	if request.method == 'POST':
		#try:
			cursor = connections['default'].cursor()
			condicion=""
			groupby="GROUP BY "
			orderby=" order by codigo_departamento asc "
			por_municipio=False
			por_centro=False
			por_nivel=False
			por_tipo_centro=False
			por_jornada=False

			if request.POST.get('nombre_centro') != '':
				reporteObject=centro_educativo.objects.filter(nombre__contains=request.POST.get('nombre_centro').strip().upper()).distinct('codigo')

			if 1 == 1:
				query="""

				SELECT codigo_departamento, departamento, count(distinct t.codigo) centros"""

				for row in request.POST.getlist('periodo'):
					query += ", ROUND(AVG(total_si_"+ str(row) +"),0) as total_si_"+ str(row) +", ROUND(AVG(total_no_" + str(row) + "),0) as total_no_"+str(row) + ", round(sum(total_si_"+str(row) + ")/case when sum(total_si_"+str(row) + "+total_no_"+str(row) + ") = 0 then 1 else sum(total_si_"+str(row) + "+total_no_"+str(row) + ") end *100 ,2) as eficiencia_"+str(row) + ", round(avg(total_si_"+str(row) + "+total_no_"+str(row) + ")/(SELECT dias_transcurridos("+str(row) + "))*100,2) as avance_"+str(row)

				for row in request.POST.getlist('agrupar'):
					query += row
							
				query += """ 
				FROM ( SELECT depto.codigo_departamento, depto.descripcion as departamento, muni.codigo_municipio, muni.descripcion as municipio, ce.codigo, ce.nombre, ce.nivel, ce.tipo_docente, j.descripcion as jornada"""
				for row in request.POST.getlist('periodo'):
					query += ", sum(total_si_"+ str(row) +") as total_si_"+ str(row) +", sum(total_no_" + str(row) + ") as total_no_"+str(row)
				query += """ 
FROM (
					  SELECT centro_id""" 

				# generar sums
				for row in request.POST.getlist('periodo'):
					query += ", sum(case when hubo_clases=True AND extract(YEAR from fecha)=" + str(row) + " then 1 else 0 end) as total_si_" + str(row) + ", sum(case when hubo_clases=False AND extract(YEAR from fecha)=" + str(row) + " then 1 else 0 end) as total_no_" + str(row)
					  
				query += """ FROM monitoreo_centro_semana
				WHERE extract(YEAR from fecha) IN ("""

				if len(request.POST.getlist('periodo')) > 0:
					for row in request.POST.getlist('periodo'):
						query += str(row)+","
					query=query[:len(query)-1]
					query += """) 
						"""
							
				query +=	"""  group by centro_id 
					  )y
					  INNER JOIN monitoreo_centro_voluntario cv ON cv.id=y.centro_id
					  INNER JOIN general_jornada j ON j.id=cv.jornada_id
					  """

				query += """
					  INNER JOIN general_centro_educativo ce ON ce.id=cv.centro_id
					  INNER JOIN general_departamento depto ON depto.id=ce.departamento_id
					  INNER JOIN general_municipio muni ON muni.id=ce.municipio_id

					  """
				#print "agrupar", request.POST.getlist('agrupar')
				if len(request.POST.getlist('departamento')) > 0:
					condicion += " WHERE depto.id in ("
					for row in request.POST.getlist('departamento'):
						condicion += str(row)+","
					condicion=condicion[:len(condicion)-1]
					condicion += """) 
						"""

					if len(request.POST.getlist('municipio')) > 0:
						condicion += " AND muni.id in ("
						for row in request.POST.getlist('municipio'):
							condicion += str(row)+","
						condicion=condicion[:len(condicion)-1]
						condicion += """) 
						"""

					if len(request.POST.getlist('tipo_centro')) > 0:
						condicion += " AND ce.tipo_docente in ("
						for row in request.POST.getlist('tipo_centro'):
							condicion += "'" + str(row)+"',"
						condicion=condicion[:len(condicion)-1]
						condicion += """) 
						"""
					if len(request.POST.getlist('nivel')) > 0:
						condicion += " AND ce.nivel in ("
						for row in request.POST.getlist('nivel'):
							condicion += "'" + str(row.encode("utf-8"))+"',"
						condicion=condicion[:len(condicion)-1]
						condicion += """) 
						"""

					if request.POST.get('nombre_centro') != '':
						condicion += " AND ce.nombre LIKE '%"+ request.POST.get('nombre_centro').upper().encode("utf-8") +"%'"
					if request.POST.get('codigo_centro') != '':
						condicion += " AND ce.codigo LIKE '"+ request.POST.get('codigo_centro').upper().encode("utf-8") +"%'"
				else:
					if len(request.POST.getlist('tipo_centro')) > 0:
						condicion += " WHERE ce.tipo_docente in ("
						for row in request.POST.getlist('tipo_centro'):
							condicion += "'" + str(row)+"',"
						condicion=condicion[:len(condicion)-1]
						condicion += """) 
						"""

					if len(request.POST.getlist('nivel')) > 0:
						condicion += " AND ce.nivel in ("
						for row in request.POST.getlist('nivel'):
							condicion += "'" + str(row.encode("utf-8"))+"',"
						condicion=condicion[:len(condicion)-1]
						condicion += """) 
						"""

					if request.POST.get('nombre_centro') != '':
						condicion += " AND ce.nombre LIKE '%"+ request.POST.get('nombre_centro').upper().encode("utf-8") +"%'"
					if request.POST.get('codigo_centro') != '':
						condicion += " AND ce.codigo LIKE '"+ request.POST.get('codigo_centro').upper().encode("utf-8") +"%'"

				#print condicion
				query += condicion.decode("utf-8") + """
				group by depto.codigo_departamento, depto.descripcion, muni.codigo_municipio, muni.descripcion, ce.codigo, ce.nombre, ce.nivel, ce.tipo_docente, j.descripcion

				) t  """
				groupby += """codigo_departamento, departamento"""
				for row in request.POST.getlist('agrupar'):
					if row == ", codigo_municipio, municipio":
						orderby=" order by codigo_departamento, codigo_municipio asc "
						groupby += ", codigo_municipio, municipio"
					if row == ", codigo, nombre":
						groupby += ", codigo, nombre"
					if row == ", nivel":
						groupby += ", nivel"
					if row == ", tipo_docente as tipo_centro":
						groupby += ", tipo_docente"
					if row == ", jornada":
						groupby += ", jornada"

				query += groupby
				query += orderby
				
				

				#print query
				cursor.execute(query)
			reporteObject = dictfetchall(cursor)
			cursor.close()
			#print reporteObject
			cont=0
			for row in reporteObject:
				#print row[5]
				#total_si=centro_semana.objects.filter(centro__centro__pk=row[2], centro__jornada__pk=row[6], hubo_clases=True).count()
				#total_no=centro_semana.objects.filter(centro__centro__pk=row[2], centro__jornada__pk=row[6], hubo_clases=False).count()
				cont += 1
				a= dict(
					pk=cont,
					codigo_departamento= row['codigo_departamento'],
					departamento= row['departamento']
					)
				for rowe in request.POST.getlist('periodo'):
					a.update({'total_si_%s'%(str(rowe)): row['total_si_%s'%(str(rowe))]})
					a.update({'total_no_'+str(rowe): row['total_no_'+str(rowe)]})
					a.update({'eficiencia_'+str(rowe): row['eficiencia_'+str(rowe)]})
					a.update({'avance_'+str(rowe): row['avance_'+str(rowe)]})
				if row.has_key('nivel') == True:
					por_nivel = True
					a.update({'nivel': row['nivel']})
				if row.has_key('tipo_centro') == True:
					por_tipo_centro = True
					a.update({'tipo_centro': row['tipo_centro']})
				if row.has_key('jornada') == True:
					por_jornada = True
					a.update({'jornada': row['jornada']})
				if row.has_key('nivel') != True and row.has_key('tipo_centro') != True and row.has_key('jornada') != True and row.has_key('nombre') != True:
					a.update({'centros': row['centros']})
				if row.has_key('municipio') == True:
					por_municipio = True
					a.update({'codigo_municipio': row['codigo_municipio']})
					a.update({'municipio': row['municipio']})
				if row.has_key('nombre') == True:
					por_centro = True
					a.update({'codigo': row['codigo']})
					a.update({'nombre': row['nombre']})

				new_list.append(a)
			
			return HttpResponse(render_to_response('monitoreo/tabla-ajax.html', {'instancia': new_list, 'por_nivel': por_nivel, 'por_tipo_centro': por_tipo_centro, 'por_jornada': por_jornada, 'por_municipio': por_municipio, 'por_centro': por_centro, 'anio': request.POST.getlist('periodo'), 'query': query}, context_instance=RequestContext(request)))
		#except Exception, e:
		#	print e
			return HttpResponse(render_to_response('monitoreo/tabla-ajax.html', {'instancia': new_list, 'por_nivel': por_nivel, 'por_tipo_centro': por_tipo_centro, 'por_jornada': por_jornada, 'por_municipio': por_municipio, 'por_centro': por_centro, 'anio': request.POST.getlist('periodo'), 'query': query}, context_instance=RequestContext(request)))
	else:
		reporteObject=centro_educativo.objects.none()
	
	ctx={'instancia': reporteObject, 'anio': periodo.objects.all() ,'departamentos':departamento.objects.all().order_by('id'), 'municipios': municipio.objects.all(), 'request': request}
	return render_to_response('monitoreo/inicio-reportes.html', ctx, context_instance=RequestContext(request))

@permission_required('monitoreo.puede_entrar_reportes', login_url='/inicio/')
def view_reporte_nacional(request):
	ctx={}
	cursor = connections['default'].cursor()

	if request.method == 'POST':
		query = """

		SELECT d.codigo_departamento, d.descripcion,
			coalesce(round(avg(total_si),0),0) as total_si, coalesce(round(avg(total_no),0),0) as total_no
		       
		FROM (
		SELECT depto.codigo_departamento, depto.descripcion as departamento, muni.codigo_municipio, muni.descripcion, ce.codigo, ce.nombre, ce.nivel, ce.tipo_docente, j.descripcion as jornada, sum(total_si) as total_si, sum(total_no) as total_no
		FROM (
		  SELECT centro_id
		  , sum(case when hubo_clases=True AND extract(YEAR from fecha)=2014 then 1 else 0 end) as total_si
		  , sum(case when hubo_clases=False AND extract(YEAR from fecha)=2014 then 1 else 0 end) as total_no
		  FROM monitoreo_centro_semana 
		  WHERE extract(YEAR from fecha) = """ + str(request.POST.get('periodo')) + """
		  group by centro_id
		  )y
		  INNER JOIN monitoreo_centro_voluntario cv ON cv.id=y.centro_id
		  INNER JOIN general_jornada j ON j.id=cv.jornada_id
		  INNER JOIN general_centro_educativo ce ON ce.id=cv.centro_id
		  INNER JOIN general_departamento depto ON depto.id=ce.departamento_id
		  INNER JOIN general_municipio muni ON muni.id=ce.municipio_id


		 group by depto.codigo_departamento, depto.descripcion, muni.codigo_municipio, muni.descripcion, ce.codigo, ce.nombre, ce.nivel, ce.tipo_docente, j.descripcion

		) t
		right join general_departamento d on d.codigo_departamento=t.codigo_departamento
		group by d.codigo_departamento, d.descripcion
		order by d.codigo_departamento asc

		"""
	else:
		query = """

		SELECT d.codigo_departamento, d.descripcion,
			coalesce(round(avg(total_si),0),0) as total_si, coalesce(round(avg(total_no),0),0) as total_no
		       
		FROM (
		SELECT depto.codigo_departamento, depto.descripcion as departamento, muni.codigo_municipio, muni.descripcion, ce.codigo, ce.nombre, ce.nivel, ce.tipo_docente, j.descripcion as jornada, sum(total_si) as total_si, sum(total_no) as total_no
		FROM (
		  SELECT centro_id
		  , sum(case when hubo_clases=True AND extract(YEAR from fecha)=2014 then 1 else 0 end) as total_si
		  , sum(case when hubo_clases=False AND extract(YEAR from fecha)=2014 then 1 else 0 end) as total_no
		  FROM monitoreo_centro_semana 
		  WHERE extract(YEAR from fecha) = """ + str(periodo.objects.get(activo=True).anio) + """
		  group by centro_id
		  )y
		  INNER JOIN monitoreo_centro_voluntario cv ON cv.id=y.centro_id
		  INNER JOIN general_jornada j ON j.id=cv.jornada_id
		  INNER JOIN general_centro_educativo ce ON ce.id=cv.centro_id
		  INNER JOIN general_departamento depto ON depto.id=ce.departamento_id
		  INNER JOIN general_municipio muni ON muni.id=ce.municipio_id


		 group by depto.codigo_departamento, depto.descripcion, muni.codigo_municipio, muni.descripcion, ce.codigo, ce.nombre, ce.nivel, ce.tipo_docente, j.descripcion

		) t
		right join general_departamento d on d.codigo_departamento=t.codigo_departamento
		group by d.codigo_departamento, d.descripcion
		order by d.codigo_departamento asc

		"""
	cursor.execute(query)
	reporteObject = dictfetchall(cursor)
	cursor.close()
	print reporteObject
	

	if request.method == 'GET':
		ctx={'data': reporteObject, 'anio': periodo.objects.all().order_by('anio'), 'periodo':periodo.objects.get(activo=True).anio}
		return render_to_response('monitoreo/inicio-reportes-nacional.html', ctx, context_instance=RequestContext(request))
	else:
		ctx={'data': reporteObject, 'anio': periodo.objects.all().order_by('anio'), 'periodo': request.POST.get('periodo')}
		return HttpResponse(render_to_response('monitoreo/grafico-reportes-nacional.html', ctx, context_instance=RequestContext(request)))


@permission_required('monitoreo.puede_entrar_reportes', login_url='/inicio/')
def view_reporte_municipal(request):
	ctx={}
	cursor = connections['default'].cursor()

	if request.method == 'POST':
		anio= str(request.POST.get('periodo'))
		filtro=""
		print request.POST.getlist('municipio[]')
		for row in request.POST.getlist('municipio[]'):
			filtro += str(row)+","
		
		if filtro == "":
			filtro="1,9,19,40,63,75,91,110,138,144,161,165,184,212,228,251,279,288"
		else:
			filtro=filtro[:len(filtro)-1]
	else:
		anio= str(periodo.objects.get(activo=True).anio)
		filtro="1,9,19,40,63,75,91,110,138,144,161,165,184,212,228,251,279,288"

	query = """

		SELECT d.codigo_departamento, d.descripcion departamento, m.codigo_municipio, municipio,
			coalesce(round(avg(total_si),0),0) as total_si, coalesce(round(avg(total_no),0),0) as total_no
		       
		FROM (
		SELECT depto.codigo_departamento, depto.descripcion as departamento, muni.departamento_id, muni.id as municipio_id,  muni.codigo_municipio, muni.descripcion as municipio, ce.codigo, ce.nombre, ce.nivel, ce.tipo_docente, j.descripcion as jornada, sum(total_si) as total_si, sum(total_no) as total_no
		FROM (
		  SELECT centro_id
		  , sum(case when hubo_clases=True AND extract(YEAR from fecha)=%s then 1 else 0 end) as total_si
		  , sum(case when hubo_clases=False AND extract(YEAR from fecha)=%s then 1 else 0 end) as total_no
		  FROM monitoreo_centro_semana 
		  WHERE extract(YEAR from fecha) = %s
		  group by centro_id
		  )y
		  INNER JOIN monitoreo_centro_voluntario cv ON cv.id=y.centro_id
		  INNER JOIN general_jornada j ON j.id=cv.jornada_id
		  INNER JOIN general_centro_educativo ce ON ce.id=cv.centro_id
		  INNER JOIN general_departamento depto ON depto.id=ce.departamento_id
		  right JOIN general_municipio muni ON muni.id=ce.municipio_id

		  where muni.id in (%s)


		 group by depto.codigo_departamento, depto.descripcion, muni.departamento_id, muni.id, muni.codigo_municipio, muni.descripcion, ce.codigo, ce.nombre, ce.nivel, ce.tipo_docente, j.descripcion

		) t
		inner join general_departamento d on d.id=t.departamento_id
		inner join general_municipio m on m.id=t.municipio_id
		group by d.codigo_departamento, d.descripcion, m.codigo_municipio, municipio
		order by d.codigo_departamento asc
	"""%(anio,anio,anio, filtro)
	cursor.execute(query)
	reporteObject = dictfetchall(cursor)
	cursor.close()
	print query

	if request.method == 'GET':
		ctx={'data': reporteObject, 'anio': periodo.objects.all().order_by('anio'), 'periodo':periodo.objects.get(activo=True).anio, 'departamentos': departamento.objects.all().order_by('id')}
		return render_to_response('monitoreo/inicio-reportes-municipal.html', ctx, context_instance=RequestContext(request))
	else:
		ctx={'data': reporteObject, 'anio': periodo.objects.all().order_by('anio'), 'periodo': request.POST.get('periodo'), 'departamentos': departamento.objects.all().order_by('id')}
		return HttpResponse(render_to_response('monitoreo/grafico-reportes-municipal.html', ctx, context_instance=RequestContext(request)))