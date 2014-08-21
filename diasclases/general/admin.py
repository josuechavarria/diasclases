from django.contrib import admin

from models import *
# Register your models here.
class voluntarioAdmin(admin.ModelAdmin):
	def formfield_for_foreignkey(self, ac_usuario_creador, request, **kwargs):
		if ac_usuario_creador.name == 'usuario_creador' or ac_usuario_creador.name == 'usuario_modificador':
			kwargs['initial'] = request.user.id
			return ac_usuario_creador.formfield(**kwargs)
		return super(voluntarioAdmin, self).formfield_for_foreignkey(
			ac_usuario_creador, request, **kwargs
		)
	list_display = ['departamento', 'municipio', 'identidad', 'nombre_completo']
	search_fields = ('identidad', 'primer_nombre', 'segundo_nombre', 'primer_apellido', 'segundo_apellido')

admin.site.register(periodo)
admin.site.register(tipo_persona)
admin.site.register(organizacion)
admin.site.register(voluntario, voluntarioAdmin)