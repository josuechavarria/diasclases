#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from diasclases.general.models import *
from django.core.exceptions import ValidationError
# Create your models here.


class centro_voluntario(models.Model):
	periodo=models.ForeignKey(periodo)
	centro=models.ForeignKey(centro_educativo)
	voluntario=models.ForeignKey(voluntario)
	jornada=models.ForeignKey(jornada)

	class Meta:
		unique_together = ('periodo','centro','jornada')

	def unique_error_message(self, model_class, unique_check):
		if model_class == type(self) and unique_check == ('periodo','centro','jornada'):
			return 'Este centro en esta jornada ya tiene un voluntario asignado.'
		else:
			return super(centro_voluntario, self).unique_error_message(model_class, unique_check)

class calendario_academico(models.Model):
	numero_semana=models.IntegerField()
	fecha_inicio=models.DateField(unique=True)
	fecha_fin=models.DateField(unique=True)

	def clean(self):
		if((self.fecha_fin - timedelta(days=5)) != self.fecha_inicio):
			raise ValidationError("La semana debe durar 6 días.")
		if(self.fecha_fin <= self.fecha_inicio):
			raise ValidationError("La fecha fin no puede ser menor que la fecha de inicio.")

	def __unicode__(self):
		return "Semana del " + str(self.fecha_inicio.strftime("%d-%b-%Y")) + " al " + str(self.fecha_fin.strftime("%d-%b-%Y"))

class razones(models.Model):
	descripcion=models.CharField(max_length=256)

	def __unicode__(self):
		return self.descripcion

class centro_semana(models.Model):
	centro=models.ForeignKey(centro_voluntario)
	semana=models.ForeignKey(calendario_academico)
	fecha=models.DateField()
	hubo_clases=models.BooleanField()
	razon=models.ForeignKey(razones, null=True, blank=True, default=None)
	usuario_creador=models.ForeignKey(User, related_name='cs_usuario_creador')
	fecha_creacion=models.DateField(default=datetime.now())
	usuario_modificador=models.ForeignKey(User, related_name='cs_usuario_modificador')
	fecha_modificacion=models.DateField(default=datetime.now())

	class Meta:
		unique_together = ('centro','semana','fecha')
		permissions = (
			("puede_descargar_excel", "Puede descargar formato de excel"),
			("puede_cargar_excel", "Puede cargar formato de excel"),
			("puede_consultar_boletas", "Puede consultar info de boletas"),
			("puede_entrar_reportes", "Puede entrar al modulo de reportes"),
		)

	def unique_error_message(self, model_class, unique_check):
		if model_class == type(self) and unique_check == ('centro','semana','fecha'):
			return 'Esta semana ya se reportó, por favor elija otra e inténtelo nuevamente.'
		else:
			return super(centro_semana, self).unique_error_message(model_class, unique_check)


