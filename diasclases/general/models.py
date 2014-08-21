#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

# Create your models here.

class periodo(models.Model):
	anio=models.IntegerField()
	descripcion=models.CharField(max_length=256)
	activo=models.BooleanField()

	def __unicode__(self):
		return self.descripcion

class  departamento(models.Model):
	codigo_departamento=models.CharField(max_length=4, unique=True)
	descripcion=models.CharField(max_length=64, verbose_name="descripción")

	def __unicode__(self):
		return '%s | %s' % (self.codigo_departamento,self.descripcion)

	
class municipio(models.Model):
	codigo_municipio=models.CharField(max_length=4)
	descripcion=models.CharField(max_length=64, verbose_name="descripción")
	departamento=models.ForeignKey(departamento)

	def __unicode__(self):
		return '%s | %s' % (self.codigo_municipio,self.descripcion)

	class Meta:
		unique_together = ('codigo_municipio','departamento')


class aldea(models.Model):
	codigo_departamento=models.CharField(max_length=4)
	codigo_municipio=models.CharField(max_length=4)
	codigo_aldea=models.CharField(max_length=4)
	descripcion=models.CharField(max_length=255, verbose_name="descripción")
	municipio=models.ForeignKey(municipio)

	def __unicode__(self):
		return '%s | %s' % (self.codigo_aldea,self.descripcion)

	class Meta:
		unique_together = ('codigo_departamento','codigo_municipio', 'codigo_aldea')

	def unique_error_message(self, model_class, unique_check):
		if model_class == type(self) and unique_check == ('codigo_departamento','codigo_municipio', 'codigo_aldea'):
			return 'Ya existe esta aldea para el municipio y departamento especificado.'
		else:
			return super(aldea, self).unique_error_message(model_class, unique_check)

class  tipo_persona(models.Model):
	descripcion=models.CharField(max_length=64, verbose_name="descripción")

	def __unicode__(self):
		return self.descripcion

class  jornada(models.Model):
	descripcion=models.CharField(max_length=64, verbose_name="descripción")

	def __unicode__(self):
		return self.descripcion

class organizacion(models.Model):
	descripcion=models.CharField(max_length=256, verbose_name="descripción")

	def __unicode__(self):
		return self.descripcion

class centro_educativo(models.Model):
	anio=models.IntegerField()
	codigo=models.CharField(max_length=12)
	nombre=models.CharField(max_length=512)
	departamento=models.ForeignKey(departamento)
	municipio=models.ForeignKey(municipio)
	aldea=models.ForeignKey(aldea)
	direccion=models.CharField(max_length=512)
	nivel=models.CharField(max_length=64)
	tipo_centro=models.CharField(max_length=128)
	tipo_docente=models.CharField(max_length=16)
	matriculaf=models.IntegerField(null=True, blank=True, default=None)
	matriculam=models.IntegerField(null=True, blank=True, default=None)
	en_funcionamiento=models.BooleanField()
	def __unicode__(self):
		return '%s | %s | %s' % (self.codigo,self.nombre, self.nivel)

class voluntario(models.Model):
	departamento=models.ForeignKey(departamento)
	municipio=models.ForeignKey(municipio)
	aldea=models.ForeignKey(aldea, null=True, blank=True, default=None)
	identidad=models.CharField(max_length=13, unique=True)
	primer_nombre=models.CharField(max_length=64)
	segundo_nombre=models.CharField(max_length=64, null=True, blank=True, default=None)
	primer_apellido=models.CharField(max_length=64)
	segundo_apellido=models.CharField(max_length=64)
	sexo=models.CharField(max_length=1)
	fecha_nacimiento=models.DateField(null=True, blank=True, default=None)
	telefono=models.CharField(max_length=8)
	tipo_persona=models.ForeignKey(tipo_persona)
	organizacion=models.ForeignKey(organizacion)
	centros=models.ManyToManyField(centro_educativo)
	activo=models.BooleanField()
	usuario_creador=models.ForeignKey(User, related_name='pe_usuario_creador')
	fecha_creacion=models.DateField(default=datetime.now())
	usuario_modificador=models.ForeignKey(User, related_name='pe_usuario_modificador')
	fecha_modificacion=models.DateField(default=datetime.now())

	def _get_full_name(self):
		"Returns the person's full name."
		return '%s %s %s %s' % (self.primer_nombre, self.segundo_nombre, self.primer_apellido, self.segundo_apellido)
	nombre_completo = property(_get_full_name)

	def __unicode__(self):
		return '%s - %s' % (self.identidad,self.nombre_completo)