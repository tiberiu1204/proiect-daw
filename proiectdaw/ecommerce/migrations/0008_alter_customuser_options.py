# Generated by Django 5.1.2 on 2024-12-10 20:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0007_alter_customuser_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='customuser',
            options={'permissions': [('vizualizeaza_oferta', 'Poate vizualiza oferta reducere 50%'), ('change_nume', 'Poate edita nume'), ('change_prenume', 'Poate edita prenume'), ('change_email', 'Poate e-mail'), ('change_blocat', 'Poate edita blocat')]},
        ),
    ]
