
from django.contrib.auth.admin  import UserAdmin as BaseUserAdmin
from django.contrib import admin
from . import models
from django.utils.translation import gettext_lazy as _
# Register your models here.

class UserAdmin(BaseUserAdmin):
    ordering = ['id']
    list_display = ['email', 'name']
    fieldsets = (
        (_('Basic Info'), {
            "fields": (
                'name', 
                'email'
            ),
        }),
        (_('Permission'), {
            'fields':(
                'is_active',
                'is_staff',
                'is_superuser',
            )
        }),
        (_('Important Dates'), {'fields': ('last_login',)}),
    )
    readonly_fields = ['last_login']

    add_fieldsets = (
        (None , {
            'classes': ('wide',),
            'fields': (
                'email',
                'password1',
                'password2',
                'name',
                'is_active',
                'is_staff',
                'is_superuser',
            )
        }),
    )
    

admin.site.register(models.User, UserAdmin)
admin.site.register(models.Recipe)