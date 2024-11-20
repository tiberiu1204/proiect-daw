from django import forms
from .models import Categorie, Produs
from django.core.exceptions import ValidationError
import re
from datetime import date, datetime


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


def text_validator(value):
    if not value.istitle() or not value.replace(' ', '').isalpha():
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
    pret_discount = forms.DecimalField(
        max_digits=10, decimal_places=2, required=False, help_text="Introduceți discount-ul (în %) pentru produs.")

    class Meta:
        model = Produs
        fields = ['nume_produs', 'descriere', 'pret', 'categorie']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nume_produs'].label = "Numele Produsului"
        self.fields['nume_produs'].error_messages = {
            'required': 'Acest câmp este obligatoriu!'}
        self.fields['descriere'].label = "Descriere Produs"
        self.fields['pret'].label = "Preț Produs"
        self.fields['categorie'].label = "Categorie Produs"

    def clean_pret(self):
        pret = self.cleaned_data.get('pret')
        if pret <= 0:
            raise forms.ValidationError(
                "Prețul trebuie să fie mai mare decât 0.")
        return pret

    def clean(self):
        cleaned_data = super().clean()
        pret = cleaned_data.get("pret")
        pret_discount = cleaned_data.get("pret_discount")

        if pret_discount is not None and (pret_discount < 0 or pret_discount > 100):
            self.add_error('pret_discount',
                           "Discount-ul trebuie să fie între 0 și 100.")

        if pret_discount is not None and pret is not None:
            if pret_discount > 0 and pret < (pret * (1 - pret_discount / 100)):
                self.add_error(
                    'pret', "Prețul nu poate fi mai mic decât prețul cu discount aplicat.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data.get('pret_discount'):
            discount = self.cleaned_data.get('pret_discount')
            instance.pret = instance.pret * (1 - discount / 100)
        if commit:
            instance.save()
        return instance
