from django.contrib import admin
from .models import Categorie, Produs, Stoc, Furnizor, Comanda, ComandaProdus, Evaluare

admin.site.site_header = "Administrare Magazin Online"
admin.site.site_title = "Panou Admin - Magazin Online"
admin.site.index_title = "Administrare Bază de Date"


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
