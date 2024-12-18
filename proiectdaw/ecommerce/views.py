from django.template.loader import render_to_string
from django.http import HttpResponseForbidden, JsonResponse
from django.core.mail import EmailMessage, send_mass_mail, mail_admins
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
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, CustomAuthenticationForm, CustomPasswordChangeForm, PromotieForm
from django.core.paginator import Paginator
from .models import CustomUser, Produs, Vizualizare, Promotie, Categorie
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Count
from django.utils.html import strip_tags
from django.utils.timezone import now
from django.core.exceptions import ValidationError
import logging
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.contrib.auth.models import Permission


logger = logging.getLogger('django')


def homepage(request):
    logger.info("Cineva a accesat /")
    if request.user.is_authenticated:
        return redirect('/profile')
    else:
        return redirect('/login')


def filtru_produse(request):
    logger.info("Cineva a accesat /produse")

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

    N = 10

    if request.user.is_authenticated:
        for produs in page_obj:
            Vizualizare.objects.update_or_create(
                utilizator=request.user,
                produs=produs,
            )
        vizualizari = Vizualizare.objects.filter(utilizator=request.user)
        if vizualizari.count() > N:
            ids_to_delete = Vizualizare.objects.values_list('id', flat=True)[
                N:]
            Vizualizare.objects.filter(id__in=ids_to_delete).delete()

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
        'user': request.user
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
                json.dump(mesaj_data, f)

            return render(request, 'contact_succes.html')

    else:
        form = ContactForm()

    return render(request, 'contact.html', {'form': form})


@login_required
def adauga_produs(request):
    if not request.user.has_perm('ecommerce.add_produs'):
        return HttpResponseForbidden(
            render(request, '403.html', {
                'user': request.user,
                'titlu': 'Eroare adăugare produse',
                'mesaj_personalizat': 'Nu ai voie să adaugi produse pe site.'
            })
        )
    form = ProdusForm()
    if request.method == 'POST':
        form = ProdusForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/filtru_produse')

    return render(request, 'adauga_produs.html', {'form': form})


def imparte_la_0():
    try:
        result = 10 / 0
        return result
    except Exception as e:
        error_message = str(e)
        mail_admins(
            subject="Eroare în aplicație",
            message=f"Eroare: {error_message}",
            html_message=f"<h1 style='color: red;'>Eroare în aplicație</h1><div style='background-color: red; color: white'>{
                error_message}</div>",
        )
        return None


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
        logger.debug(f"Confirmation sent to {dest}")

    if request.user.is_authenticated:
        return redirect('/profile')
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)

        username = request.POST.get('username')
        email = request.POST.get('email')
        if username.lower() == 'admin':
            logger.critical("Un borfas incearca sa ne fure")
            mail_admins(
                subject="Cineva incearca sa ne preia site-ul",
                message=f"Email: {email}",
                html_message=f"<h1 style='color: red;'>Cineva incearca sa ne preia site-ul</h1> \
                        <p>Email: {email}</p>",
            )
            try:
                raise ValidationError("Nu mai fura ba bborfasule!")
            except Exception as e:
                error_message = str(e)
                mail_admins(
                    subject="Eroare în aplicație",
                    message=f"Eroare: {error_message}",
                    html_message=f"<h1 style='color: red;'>Eroare în aplicație</h1><div style='background-color: red; color: white'>{
                        error_message}</div>",
                )
                logger.critical("Un borfas a fost identificat cu succes")

        elif form.is_valid():
            logger.debug("User form is valid")
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
            return redirect('/confirmation-sent')
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
        logger.error("Userul nu exista")
        return render(request, "404.html")


failed_logins = {}


def login_view(request):
    global failed_logins

    if request.user.is_authenticated:
        return redirect('/profile')
    if request.method == 'POST':
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            failed_logins.pop(user.username, None)
            if not user.email_confirmat:
                logger.error("Userul nu a fost confirmat")
                return render(request, 'login.html', {'form': form, 'error': "Eroare: Emailul dvs. nu a fost confirmat"})
            if user.blocat:
                return HttpResponseForbidden(render(request, '403.html', {
                    'user': request.user,
                    'titlu': 'Cont blocat',
                    'mesaj_personalizat': 'Contul dvs este blocat'
                }))
            if not form.cleaned_data.get('remember_me'):
                request.session.set_expiry(0)
            else:
                request.session.set_expiry(86400)
            login(request, user)
            request.session['user_data'] = {
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
            return redirect('/profile')
        else:
            username = request.POST.get('username')
            failed_logins[username] = failed_logins.get(username, [])
            failed_logins[username].append(now())
            failed_logins[username] = [
                t for t in failed_logins[username]
                if (now() - t).seconds < 120
            ]
            logger.warning(f"Userul {username} nu a reusit sa se logheze")
            if len(failed_logins[username]) >= 3:
                mail_admins(
                    subject="Logari suspecte",

                    message=f"Logari suspecte\n \
                    Username: {username}\n \
                    Ip: {request.META.get('REMOTE_ADDR')}",

                    html_message=f"<h1 style='colusernameor: red;'>Logari suspecte</h1> \
                    <p>Username: {username}</p> \
                    <p>Ip: {request.META.get('REMOTE_ADDR')}</p>",
                )
                logger.warning(
                    f"Activitate suspicioasa pentru userul {username}")

    else:
        form = CustomAuthenticationForm()
    return render(request, 'login.html', {'form': form})


def confirmation_view(request):
    return render(request, 'confirmation_sent.html')


def logout_view(request):
    permission = Permission.objects.get(codename='vizualizeaza_oferta')
    request.user.user_permissions.remove(permission)
    logout(request)
    return redirect('/login')


@login_required
def profile_view(request):
    if not request.user.is_authenticated:
        return redirect('/login')

    user_data = request.session['user_data']
    return render(request, 'profile.html', {'user_data': user_data})


@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('/profile')
    else:
        form = CustomPasswordChangeForm(user=request.user)
    return render(request, 'change_password.html', {'form': form})


@login_required
def promotii(request):
    if request.method == 'POST':
        form = PromotieForm(request.POST)
        if form.is_valid():
            promotie = form.save()

            K = 5

            email_messages = []
            for categorie in promotie.categorii.all():

                utilizatori = (
                    Vizualizare.objects
                    .filter(produs__categorie=categorie)
                    .values('utilizator')
                    .annotate(vizualizari_count=Count('id'))
                    .filter(vizualizari_count__gte=K)
                )

                utilizatori_emails = [
                    CustomUser.objects.get(id=utilizator['utilizator']).email
                    for utilizator in utilizatori
                ]

                if utilizatori_emails:
                    for email in utilizatori_emails:
                        if categorie.nume_categorie == 'Auto':
                            template_name = 'promotie_auto.html'
                        elif categorie.nume_categorie == 'Electronice':
                            template_name = 'promotie_electronice.html'
                        else:
                            continue

                        context = {
                            'subiect': promotie.subiect,
                            'procent_discount': promotie.procent_discount,
                            'data_expirare': promotie.data_expirare
                        }

                        email_content = render_to_string(
                            template_name, context)
                        email_subject = f"O nouă promoție pentru produsele din categoria {
                            categorie.nume_categorie}"
                        message = (email_subject, email_content,
                                   'proiect.daw.node@gmail.com', [email])

                        email_messages.append(message)

            if email_messages:
                send_mass_mail(email_messages)

            return redirect('/produse')
    else:
        form = PromotieForm()

    return render(request, 'promotii.html', {'form': form})


@receiver(user_logged_in)
def save_user_data_in_session(sender, request, user, **kwargs):
    request.session['user_data'] = {
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


def aloca_permisiune_oferta(request):
    if request.method == "POST":
        permission = Permission.objects.get(codename='vizualizeaza_oferta')
        if request.user.is_authenticated:
            request.user.user_permissions.add(permission)
            return JsonResponse({"success": True})

    return JsonResponse({"success": False}, status=400)


def oferta(request):
    if not request.user.has_perm('ecommerce.vizualizeaza_oferta'):
        return HttpResponseForbidden(render(request, '403.html', {
            'user': request.user,
            'titlu': 'Eroare afisare oferta',
            'mesaj_personalizat': 'Nu ai voie să vizualizezi oferta'
        }))
    return render(request, 'oferta.html')
