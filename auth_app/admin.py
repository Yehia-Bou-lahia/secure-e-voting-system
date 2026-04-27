from django.contrib import admin
from .models import ElectionSettings
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

@admin.register(ElectionSettings)
class ElectionSettingsAdmin(admin.ModelAdmin):
    list_display = ('start_time', 'end_time', 'updated_at')
    # منع إضافة أكثر من سجل (يجب أن يكون هناك سجل واحد فقط)
    def has_add_permission(self, request):
        # إذا كان هناك سجل موجود، لا تسمح بإضافة آخر
        if ElectionSettings.objects.exists():
            return False
        return super().has_add_permission(request)