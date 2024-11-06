from django.contrib import admin
from .models import Categorie, Produs, Stoc, Furnizor, Comanda, ComandaProdus, Evaluare

admin.site.register(Categorie)
admin.site.register(Produs)
admin.site.register(Stoc)
admin.site.register(Furnizor)
admin.site.register(Comanda)
admin.site.register(ComandaProdus)
admin.site.register(Evaluare)

# Register your models here.
