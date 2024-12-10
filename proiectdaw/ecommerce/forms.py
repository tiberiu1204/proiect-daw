from .models import Categorie
from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from .models import Categorie, Produs
from django.core.exceptions import ValidationError
import re
from datetime import date, datetime
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Promotie


class FiltruProduseForm(forms.Form):
    nume_produs = forms.CharField(
        max_length=100, required=False, label='Nume produs')
    pret_min = forms.DecimalField(
        max_digits=10, decimal_places=2, required=False, label='Preț minim')
    pret_max = forms.DecimalField(
        max_digits=10, decimal_places=2, required=False, label='Preț maxim')
    categorie = forms.ModelChoiceField(
        queryset=Categorie.objects.all(),
        required=False,
        empty_label="Toate categoriile",
        label='Categorie'
    )


def text_validator(value: str):
    if not value:
        return
    if not value[0].isupper() or not value.replace(' ', '').isalpha():
        raise ValidationError(
            'Textul trebuie să înceapă cu literă mare și să conțină doar litere și spații.')


def calculate_age(birth_date):
    today = date.today()
    years = today.year - birth_date.year
    months = today.month - birth_date.month
    if months < 0:
        years -= 1
        months += 12
    return f"{years} ani și {months} luni"


class ContactForm(forms.Form):
    TIP_MESAJ_CHOICES = [
        ('reclamatie', 'Reclamație'),
        ('intrebare', 'Întrebare'),
        ('review', 'Review'),
        ('cerere', 'Cerere'),
        ('programare', 'Programare'),
    ]

    nume = forms.CharField(
        max_length=10,
        required=True,
        label="Nume",
        validators=[text_validator]
    )
    prenume = forms.CharField(
        max_length=50,
        required=False,
        label="Prenume",
        validators=[text_validator]
    )
    data_nasterii = forms.DateField(
        required=False,
        label="Data nașterii",
        widget=forms.SelectDateWidget(years=range(1900, date.today().year + 1))
    )
    email = forms.EmailField(
        required=True,
        label="E-mail"
    )
    confirmare_email = forms.EmailField(
        required=True,
        label="Confirmare E-mail"
    )
    tip_mesaj = forms.ChoiceField(
        choices=TIP_MESAJ_CHOICES,
        label="Tip mesaj",
        required=True
    )
    subiect = forms.CharField(
        required=True,
        max_length=100,
        label="Subiect",
        validators=[text_validator]
    )
    minim_zile_asteptare = forms.IntegerField(
        required=True,
        label="Minim zile așteptare",
        min_value=1
    )
    mesaj = forms.CharField(
        required=True,
        widget=forms.Textarea,
        label="Mesaj (semnează-te la final)"
    )

    def clean(self):
        cleaned_data = super().clean()

        email = cleaned_data.get("email")
        confirmare_email = cleaned_data.get("confirmare_email")
        if email != confirmare_email:
            raise ValidationError(
                "E-mailul și confirmarea e-mailului trebuie să coincidă.")
        data_nasterii = cleaned_data.get("data_nasterii")
        if data_nasterii:
            age = (date.today() - data_nasterii).days // 365.25
            if age < 18:
                raise ValidationError(
                    "Trebuie să fiți major pentru a trimite mesajul.")

        mesaj = cleaned_data.get("mesaj")
        if mesaj:
            words = re.findall(r'\b\w+\b', mesaj)
            if len(words) < 5 or len(words) > 100:
                raise ValidationError(
                    "Mesajul trebuie să conțină între 5 și 100 de cuvinte.")
            if any(word.startswith("http://") or word.startswith("https://") for word in words):
                raise ValidationError("Mesajul nu poate conține linkuri.")
            nume = cleaned_data.get("nume")
            if nume and not mesaj.strip().endswith(nume):
                raise ValidationError(
                    "Mesajul trebuie să se termine cu semnătura dumneavoastră.")

        return cleaned_data


class ProdusForm(forms.ModelForm):
    discount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        help_text="Introduceți discount-ul (în %) pentru produs."
    )
    pret_baza = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True
    )

    class Meta:
        model = Produs
        fields = ['nume_produs', 'descriere', 'categorie']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nume_produs'].label = "Numele Produsului"
        self.fields['nume_produs'].error_messages = {
            'required': 'Acest câmp este obligatoriu!'}
        self.fields['descriere'].label = "Descriere Produs"
        self.fields['descriere'].error_messages = {
            'required': 'Acest câmp este obligatoriu!'}
        self.fields['categorie'].label = "Categorie Produs"
        self.fields['categorie'].error_messages = {
            'required': 'Acest câmp este obligatoriu!'}

    def clean_pret_baza(self):
        pret_baza = self.cleaned_data.get('pret_baza')
        if pret_baza <= 0:
            raise forms.ValidationError(
                "Prețul de baza trebuie să fie mai mare decât 0.")
        return pret_baza

    def clean(self):
        cleaned_data = super().clean()
        pret_baza = cleaned_data.get("pret_baza")
        discount = cleaned_data.get("discount")
        nume_produs = cleaned_data.get("nume_produs")

        if not nume_produs[0].isupper():
            self.add_error('nume_produs',
                           "Numele produsului trebuie sa inceapa cu litera mare.")

        if discount is not None and (discount < 0 or discount > 100):
            self.add_error('discount',
                           "Discount-ul trebuie să fie între 0 și 100.")

        if discount is not None and pret_baza is not None:
            if pret_baza * discount / 100 > 1000:
                self.add_error(
                    'discount', "Cuantumul reducerii nu poate depasii 1000 RON.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data.get('discount'):
            discount = self.cleaned_data.get('discount')
            instance.pret = self.cleaned_data.get(
                'pret_baza') * (1 - discount / 100)
        if commit:
            instance.save()
        return instance


class CustomUserModeratorFrom(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['last_name', 'first_name', 'email', 'blocat']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user:
            if not self.user.has_perm('ecommerce.change_user'):
                for field in self.fields:
                    field.widget.attrs['readonly'] = True
            if self.user.has_perm('ecommerce.moderator'):
                self.fields['last_name'].widget.attrs['readonly'] = True
                self.fields['first_name'].widget.attrs['readonly'] = True
                self.fields['email'].widget.attrs['readonly'] = True
                self.fields['blocat'].widget.attrs['readonly'] = True


class CustomUserCreationForm(UserCreationForm):
    phone_number = forms.CharField(required=True, max_length=15)
    address = forms.CharField(widget=forms.Textarea, required=True)
    city = forms.CharField(max_length=100, required=True)
    date_of_birth = forms.DateField(
        required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    is_seller = forms.BooleanField(required=False)
    cod = None
    email_confirmat = False

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'username', 'email', 'phone_number', 'address',
                  'city', 'date_of_birth', 'is_seller', 'password1', 'password2']

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if not phone.isdigit():
            raise forms.ValidationError(
                "Numărul de telefon trebuie să conțină doar cifre.")
        return phone

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        from datetime import date
        if dob >= date.today():
            raise forms.ValidationError(
                "Data nașterii trebuie să fie în trecut.")
        return dob

    def clean_city(self):
        city = self.cleaned_data.get('city')
        if len(city) < 3:
            raise forms.ValidationError(
                "Orașul trebuie să aibă cel puțin 3 caractere.")
        return city


class CustomAuthenticationForm(AuthenticationForm):
    remember_me = forms.BooleanField(required=False, label="Ține-mă minte")


class CustomPasswordChangeForm(PasswordChangeForm):
    pass


class PromotieForm(forms.ModelForm):
    class Meta:
        model = Promotie
        fields = ['nume', 'subiect', 'data_expirare',
                  'categorii', 'procent_discount']
        widgets = {
            'data_expirare': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    categorii = forms.ModelMultipleChoiceField(
        queryset=Categorie.objects.filter(
            nume_categorie__in=['Auto', 'Electronice']),
        widget=forms.CheckboxSelectMultiple,
        label="Categorii"
    )
