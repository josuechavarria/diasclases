#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from django import forms
from django.forms import ModelForm, formsets, fields
from django.contrib.auth.models import User
from diasclases.general.models import voluntario, tipo_persona, departamento, municipio, aldea, periodo
from diasclases.monitoreo.models import calendario_academico


class FormLogin(forms.Form):
	username = forms.CharField(label="Usuario",widget = forms.TextInput(attrs={'placeholder':'Usuario', 'required':'required', 'class': 'form-control'}))
	password = forms.CharField(label="Contraseña", widget = forms.PasswordInput(attrs={'placeholder': 'Contraseña', 'required':'required', 'class': 'form-control'}))

class PersonaForm(ModelForm):
	class Meta:
		model = voluntario
		exclude = ('activo','usuario_creador', 'fecha_creacion', 'usuario_modificador', 'fecha_modificacion')
	sexo_CHOICES = (('F', 'Femenino'),('M', 'Masculino'))
	sexo = forms.ChoiceField(label='Genero:', required=True, choices=sexo_CHOICES, initial=False)
	departamento = forms.ModelChoiceField(label="Departamento", queryset=departamento.objects.all().order_by('id'), widget=forms.Select(attrs={'required':'required'}))
	tipo_persona = forms.ModelChoiceField(label="Esta persona es un(a)", queryset=tipo_persona.objects.filter(pk=1), widget=forms.Select(attrs={'required':'required'}))

class DepartamentoForm(forms.Form):
	departamento = forms.ModelChoiceField(label="Departamento", queryset=departamento.objects.all().order_by('id'), widget=forms.Select(attrs={'required':'required'}))
	municipio = forms.ModelChoiceField(label="Municipio", queryset=municipio.objects.all().order_by('codigo_municipio'), required=False)
	aldea = forms.ModelChoiceField(label="Aldea", queryset=aldea.objects.all().order_by('codigo_aldea'), required=False)
	semana = forms.ModelChoiceField(label="Semana", queryset=calendario_academico.objects.filter(fecha_inicio__year=periodo.objects.get(activo=True).anio).order_by('numero_semana'), widget=forms.Select(attrs={'required':'required'}))
	
class ConsultaForm(forms.Form):
	departamento = forms.ModelChoiceField(label="Departamento", queryset=departamento.objects.all().order_by('id'), widget=forms.Select(attrs={'required':'required'}))
	municipio = forms.ModelChoiceField(label="Municipio", queryset=municipio.objects.all().order_by('codigo_municipio'), required=False)
	aldea = forms.ModelChoiceField(label="Aldea", queryset=aldea.objects.all().order_by('codigo_aldea'), required=False)
