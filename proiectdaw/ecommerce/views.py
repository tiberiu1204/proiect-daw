from django.template.loader import render_to_string
from django.core.mail import EmailMessage
import random
import string
from django.http import JsonResponse
from django.shortcuts import render, redirect
from .models import Produs
from .forms import FiltruProduseForm, ProdusForm
import os
import json
import time
from django.conf import settings
from .forms import ContactForm, calculate_age
import re
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, CustomAuthenticationForm, CustomPasswordChangeForm
from django.core.paginator import Paginator
from .models import CustomUser


def homepage(request):
    if request.user.is_authenticated:
        return redirect('profile')
    else:
        return redirect('login')


def filtru_produse(request):
    form = FiltruProduseForm(request.GET or None)
    produse = Produs.objects.all()

    if form.is_valid():
        nume_produs = form.cleaned_data.get('nume_produs')
        pret_min = form.cleaned_data.get('pret_min')
        pret_max = form.cleaned_data.get('pret_max')
        categorie = form.cleaned_data.get('categorie')

        if nume_produs is not None:
            produse = produse.filter(nume_produs__icontains=nume_produs)
        if pret_min is not None:
            produse = produse.filter(pret__gte=pret_min)
        if pret_max is not None:
            produse = produse.filter(pret__lte=pret_max)
        if categorie is not None:
            produse = produse.filter(categorie=categorie)

    paginator = Paginator(produse, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        produse_data = [
            {
                'nume_produs': produs.nume_produs,
                'descriere': produs.descriere,
                'pret': float(produs.pret),
            }
            for produs in page_obj
        ]
        return JsonResponse({
            'produse': produse_data,
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next(),
            'num_pages': paginator.num_pages,
            'current_page': page_obj.number,
        })

    return render(request, 'produse/filtru_produse.html', {
        'form': form,
        'produse': page_obj,
    })


def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            varsta = None
            if data['data_nasterii']:
                varsta = calculate_age(data['data_nasterii'])

            mesaj = re.sub(r'\s+', ' ', data['mesaj'].replace('\n', ' '))

            mesaj_data = {
                "nume": data['nume'],
                "prenume": data.get('prenume', ''),
                "varsta": varsta,
                "email": data['email'],
                "tip_mesaj": data['tip_mesaj'],
                "subiect": data['subiect'],
                "minim_zile_asteptare": data['minim_zile_asteptare'],
                "mesaj": mesaj
            }

            folder = os.path.join(settings.BASE_DIR, 'mesaje')
            if not os.path.exists(folder):
                os.makedirs(folder)

            timestamp = int(time.time())
            file_path = os.path.join(folder, f"mesaj_{timestamp}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(mesaj_data, f, ensure_ascii=False, indent=4)

            return render(request, 'contact_succes.html')

    else:
        form = ContactForm()

    return render(request, 'contact.html', {'form': form})


def adauga_produs(request):
    form = ProdusForm()
    if request.method == 'POST':
        form = ProdusForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('filtru_produse')
        else:
            form = ProdusForm()

    return render(request, 'adauga_produs.html', {'form': form})


def register_view(request):
    def send_confirmation_mail(context, dest):
        html_content = render_to_string('bun_venit.html', context)
        email = EmailMessage(
            subject="Bun venit!",
            body=html_content,
            to=[dest]
        )
        email.content_subtype = 'html'
        email.send(fail_silently=False)

    if request.user.is_authenticated:
        return redirect('profile')
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.instance.cod = ''.join(random.choices(string.ascii_uppercase +
                                                       string.digits, k=100))
            user = form.save()
            context = {"username": user.username,
                       "nume": user.last_name,
                       "prenume": user.first_name,
                       "site_url": request.get_host(),
                       "cod": user.cod,
                       "url_imagine": f"{request.get_host()}{settings.STATIC_URL}ecommerce/photos/cat.jpeg"}
            send_confirmation_mail(context, user.email)
            return redirect('confirmation-sent')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})


def email_confirmat(request, cod):
    try:
        user = CustomUser.objects.get(cod=cod)
        user.email_confirmat = True
        user.save()
        return render(request, 'email_confirmat.html')

    except CustomUser.DoesNotExist:
        return render(request, "404.html")


def login_view(request):
    if request.user.is_authenticated:
        return redirect('profile')
    if request.method == 'POST':
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.email_confirmat:
                return render(request, 'login.html', {'form': form, 'error': "Eroare: Emailul dvs. nu a fost confirmat"})
            login(request, user)
            if not form.cleaned_data.get('remember_me'):
                request.session.set_expiry(0)
            else:
                request.session.set_expiry(86400)
            return redirect('profile')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'login.html', {'form': form})


def confirmation_view(request):
    return render(request, 'confirmation_sent.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def profile_view(request):
    if not request.user.is_authenticated:
        return redirect('login')

    user = request.user
    user_data = {
        'prenume': user.first_name,
        'nume': user.last_name,
        'username': user.username,
        'email': user.email,
        'phone_number': user.phone_number,
        'address': user.address,
        'city': user.city,
        'date_of_birth': user.date_of_birth.strftime('%Y-%m-%d') if user.date_of_birth else None,
        'is_seller': user.is_seller,
    }
    request.session['user_data'] = user_data
    return render(request, 'profile.html', {'user_data': user_data})


@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = CustomPasswordChangeForm(user=request.user)
    return render(request, 'change_password.html', {'form': form})
