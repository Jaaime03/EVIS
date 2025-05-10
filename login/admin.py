from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

# 1) Form para crear usuarios, ahora pide email
class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

# 2) Form para editar usuarios, incluye email
class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ("username", "email", "is_active", "is_staff",
                  "is_superuser", "groups", "user_permissions")

# 3) UserAdmin “nuevo” que usa los forms anteriores y expone email
class CustomUserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm

    # Al crear usuario en admin:
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "password1", "password2"),
        }),
    )

    # Al editar usuario:
    fieldsets = (
        (None,               {"fields": ("username", "email", "password")}),
        ("Permisos",         {"fields": ("is_active", "is_staff", "is_superuser")}),
        ("Grupos y permisos",{"fields": ("groups", "user_permissions")}),
        ("Fechas importantes", {"fields": ("last_login", "date_joined")}),
    )

    list_display = ("username", "email", "is_staff", "is_active")
    list_filter  = ("is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("username", "email")
    ordering = ("username",)

# 4) “Desregistra” el admin por defecto y registra el tuyo
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
