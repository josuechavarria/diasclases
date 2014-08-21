#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from django.shortcuts import render, render_to_response
from django.template import RequestContext
from django.contrib.auth.models import Group, User
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import permission_required, login_required
from diasclases.monitoreo.forms import *
from diasclases.general.models import *
from diasclases.monitoreo.models import *
import json
from datetime import datetime, timedelta
now = datetime.now()
from django.db import transaction, IntegrityError


@login_required
@transaction.atomic
def view_reportar_semana(request):
	data=[]
	centros_data=list(centro_educativo.objects.filter(pk__in=voluntario.objects.filter(centros__anio=now.year, centros__en_funcionamiento=True).values_list('centros__pk')).values_list('id','codigo','nombre', 'nivel'))
	voluntarios_data=voluntario.objects.filter(centros__anio=now.year, centros__en_funcionamiento=True).values_list('centros__pk')
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
	print data
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
				return HttpResponseRedirect(reverse('vista_reportar_semana_centrovoluntario', args=[insert_cv.pk])) #redirecciona a la raiz
			
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

@login_required
@transaction.atomic
def view_reportar_semana_centrovoluntario(request, centro_voluntario_id):
	centrov=centro_voluntario.objects.get(pk=centro_voluntario_id)

	# armar la semana con los lunes de cada semana en un select en plantilla
	# Trae las semanas que no se han reportado del centro
	calendario=calendario_academico.objects.exclude(pk__in=centro_semana.objects.filter(centro__pk=centro_voluntario_id).values_list('semana__pk')).order_by('numero_semana')
	calendario2=calendario_academico.objects.filter(pk__in=centro_semana.objects.filter(centro__pk=centro_voluntario_id).values_list('semana__pk')).order_by('numero_semana')
	ctx = {'centro_voluntario': centrov, 'calendario': calendario, 'reportadas': calendario2}
	return render_to_response('monitoreo/reportar-semana-centrovoluntario.html', ctx, context_instance=RequestContext(request))

@login_required
@transaction.atomic
def view_semana_ajax(request, centro_voluntario_id, semana_id):
	if request.method == 'GET':
		centrov=centro_voluntario.objects.get(pk=centro_voluntario_id)
		calendario2=calendario_academico.objects.exclude(pk__in=centro_semana.objects.filter(centro__pk=centro_voluntario_id).values_list('semana__pk')).order_by('numero_semana')
		calendarioreportadas=calendario_academico.objects.filter(pk__in=centro_semana.objects.filter(centro__pk=centro_voluntario_id).values_list('semana__pk')).order_by('numero_semana')
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
			calendario_next=list(calendario_academico.objects.exclude(pk__in=centro_semana.objects.filter(centro__pk=centro_voluntario_id).values_list('semana__pk')).order_by('numero_semana')[:1])
			for ca in calendario_next:
				print ca.pk
				return HttpResponseRedirect(reverse('vista_semana_ajax', args=[centrov.pk, ca.pk]))
				break
			return HttpResponseRedirect(reverse('vista_reportar_semana_centrovoluntario', args=[centrov.pk]))


		except IntegrityError, e:
			print e
			transaction.savepoint_rollback(sid)
			calendario=calendario_academico.objects.exclude(pk__in=centro_semana.objects.filter(centro__pk=centro_voluntario_id).values_list('semana__pk')).order_by('numero_semana')
			mensaje = 'Uno de los centros seleccionados ya tiene un voluntario asignado.'
			ctx = {'error':'cx', 'errores': mensaje, 'centro_voluntario': centrov, 'calendario': calendario}
			return render_to_response('monitoreo/reportar-semana-centrovoluntario.html',ctx, context_instance=RequestContext(request))
		except Exception, e:
			print e
			transaction.savepoint_rollback(sid)
			calendario=calendario_academico.objects.exclude(pk__in=centro_semana.objects.filter(centro__pk=centro_voluntario_id).values_list('semana__pk')).order_by('numero_semana')
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
			centro_semana.objects.filter(centro=centro_voluntario_id, semana=semana_id).delete()
			transaction.savepoint_commit(sid)
		except Exception, e:
			print e
			transaction.savepoint_rollback(sid)
			
		calendario_next=list(calendario_academico.objects.exclude(pk__in=centro_semana.objects.filter(centro__pk=centro_voluntario_id).values_list('semana__pk')).order_by('numero_semana')[:1])
		for ca in calendario_next:
			print ca.pk
			return HttpResponseRedirect(reverse('vista_semana_ajax', args=[centro_voluntario_id, ca.pk]))
			break
