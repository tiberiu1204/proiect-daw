from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    is_seller = models.BooleanField(default=False)
    cod = models.CharField(max_length=100, null=True)
    email_confirmat = models.BooleanField(default=False, null=False)

    def __str__(self):
        return self.username


class Categorie(models.Model):
    nume_categorie = models.CharField(max_length=100)
    descriere_categorie = models.TextField()

    def __str__(self):
        return self.nume_categorie


class Produs(models.Model):
    nume_produs = models.CharField(max_length=100)
    descriere = models.TextField()
    pret = models.DecimalField(max_digits=10, decimal_places=2)
    categorie = models.ForeignKey(Categorie, on_delete=models.CASCADE)
    data_adaugarii = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nume_produs


class Stoc(models.Model):
    produs = models.ForeignKey(Produs, on_delete=models.CASCADE)
    cantitate = models.IntegerField()
    data_actualizarii = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Stoc pentru {self.produs.nume_produs}"


class Furnizor(models.Model):
    nume_furnizor = models.CharField(max_length=100)
    adresa_furnizor = models.TextField()
    telefon_furnizor = models.CharField(max_length=15)

    def __str__(self):
        return self.nume_furnizor


class Comanda(models.Model):
    data_comenzii = models.DateTimeField(auto_now_add=True)
    status_comanda = models.CharField(max_length=50)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Comanda #{self.id}"


class ComandaProdus(models.Model):
    comanda = models.ForeignKey(Comanda, on_delete=models.CASCADE)
    produs = models.ForeignKey(Produs, on_delete=models.CASCADE)
    cantitate = models.IntegerField()
    pret_total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.cantitate} x {self.produs.nume_produs}"


class Evaluare(models.Model):
    produs = models.ForeignKey(Produs, on_delete=models.CASCADE)
    client = models.CharField(max_length=100)
    rating = models.IntegerField()
    comentariu = models.TextField()
    data_evaluarii = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Evaluare pentru {self.produs.nume_produs} de la {self.client}"
