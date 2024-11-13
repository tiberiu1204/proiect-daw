from django.core.paginator import Paginator
from django.shortcuts import render
from .models import Produs, Categorie


def filtru_produse(request):
    produse = Produs.objects.all()

    nume_produs = request.GET.get('nume_produs')
    if nume_produs:
        produse = produse.filter(nume_produs__icontains=nume_produs)

    pret_min = request.GET.get('pret_min')
    pret_max = request.GET.get('pret_max')
    if pret_min:
        produse = produse.filter(pret__gte=pret_min)
    if pret_max:
        produse = produse.filter(pret__lte=pret_max)

    categorie_id = request.GET.get('categorie')
    if categorie_id:
        produse = produse.filter(categorie_id=categorie_id)

    paginator = Paginator(produse, 5)
    pagina_numar = request.GET.get('page')
    pagina = paginator.get_page(pagina_numar)

    return render(request, 'produse/filtru_produse.html', {
        'pagina': pagina,
        'categorii': Categorie.objects.all()
    })
