from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import Doctor, Appointment, Review, MedicalRecord, Service, CustomUser
from django.contrib.admin import AdminSite

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('role',)}),
    )


class MyAdminSite(admin.AdminSite):
    site_header = "My Admin"
    site_title = "My Admin Portal"
    index_title = "Welcome to My Admin"

    class Media:
        css = {
            'all': ('admin/css/admin_styles.css',)
        }

admin_site = MyAdminSite(name='myadmin')

admin.site.register(Service)
admin.site.register(Doctor)
admin.site.register(Appointment)
admin.site.register(Review)
admin.site.register(MedicalRecord)
admin.site.register(CustomUser, CustomUserAdmin)
