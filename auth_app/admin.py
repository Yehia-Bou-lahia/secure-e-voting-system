from django.contrib import admin

from auth_app.models import User


# Register your models here.
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'is_active', 'created_at', 'updated_at', 'role')
    search_fields = ('id', 'email')
    ordering = ('-created_at',)
    fieldsets = (
        (None, {'fields': ('email', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff')}),
    )
