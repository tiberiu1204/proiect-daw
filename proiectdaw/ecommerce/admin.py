from django.contrib import admin
from .models import Categorie, Produs, Stoc, Furnizor, Comanda, ComandaProdus, Evaluare, CustomUser
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group, Permission

admin.site.site_header = "Administrare Magazin Online"
admin.site.site_title = "Panou Admin - Magazin Online"
admin.site.index_title = "Administrare Bază de Date"

group, created = Group.objects.get_or_create(name="Moderatori")


permission_view_users = Permission.objects.get(codename='view_customuser')
permission_change_users = Permission.objects.get(codename='change_customuser')
change_nume = Permission.objects.get(codename='change_nume')
change_prenume = Permission.objects.get(codename='change_prenume')
change_email = Permission.objects.get(codename='change_email')
change_blocat = Permission.objects.get(codename='change_blocat')

if created:
    group.permissions.set(
        [change_nume, change_prenume, change_email, change_blocat, permission_view_users, permission_change_users])
    group.save()


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ["phone_number", "address", "city",
                    "date_of_birth", "is_seller", "cod", "email_confirmat"]

    add_fieldsets = (
        (None, {
            'fields': ('first_name', 'last_name', 'username', 'email', 'phone_number', 'address',
                       'city', 'date_of_birth', 'is_seller', 'password1', 'password2')
        }),
    )

    fieldsets = UserAdmin.fieldsets + (
        ('Campuri suplimentare', {
            'fields': ('phone_number', 'address', 'city', 'is_seller', 'date_of_birth', 'cod', 'email_confirmat'),
        }),
    )

    def get_fieldsets(self, request, obj=None):
        if request.user.is_superuser:
            return UserAdmin.get_fieldsets(self, request, obj)
        fields = []
        if request.user.has_perm('ecommerce.change_nume'):
            fields.append('last_name')
        if request.user.has_perm('ecommerce.change_prenume'):
            fields.append('first_name')
        if request.user.has_perm('ecommerce.change_email'):
            fields.append('email')
        if request.user.has_perm('ecommerce.change_blocat'):
            fields.append('blocat')
        return [
            (None, {'fields': tuple(fields)}),
        ]

    def has_change_permission(self, request, obj=None):
        if request.user.has_perm('ecommerce.moderator'):
            return True
        return super().has_change_permission(request, obj)


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ('id', 'nume_categorie', 'descriere_categorie')
    search_fields = ('nume_categorie',)


@admin.register(Produs)
class ProdusAdmin(admin.ModelAdmin):
    list_display = ('id', 'nume_produs', 'pret', 'categorie', 'data_adaugarii')
    search_fields = ('nume_produs',)
    list_filter = ('categorie',)
    date_hierarchy = 'data_adaugarii'

    fieldsets = (
        ('Informații Produs', {
            'fields': ('nume_produs', 'descriere', 'categorie')
        }),
        ('Preț și Data Adăugării', {
            'fields': ('pret',)
        }),
    )
    readonly_fields = ('data_adaugarii',)


@admin.register(Stoc)
class StocAdmin(admin.ModelAdmin):
    list_display = ('id', 'produs', 'cantitate', 'data_actualizarii')
    search_fields = ('produs__nume_produs',)
    list_filter = ('data_actualizarii',)


@admin.register(Furnizor)
class FurnizorAdmin(admin.ModelAdmin):
    list_display = ('id', 'telefon_furnizor', 'nume_furnizor')
    search_fields = ('nume_furnizor',)


@admin.register(Comanda)
class ComandaAdmin(admin.ModelAdmin):
    list_display = ('id', 'data_comenzii', 'status_comanda', 'total')
    search_fields = ('status_comanda',)
    list_filter = ('status_comanda',)
    date_hierarchy = 'data_comenzii'


@admin.register(ComandaProdus)
class ComandaProdusAdmin(admin.ModelAdmin):
    list_display = ('id', 'comanda', 'produs', 'cantitate', 'pret_total')
    search_fields = ('produs__nume_produs',)


@admin.register(Evaluare)
class EvaluareAdmin(admin.ModelAdmin):
    list_display = ('id', 'produs', 'client', 'rating', 'data_evaluarii')
    search_fields = ('client', 'produs__nume_produs')
    list_filter = ('rating',)
    date_hierarchy = 'data_evaluarii'
