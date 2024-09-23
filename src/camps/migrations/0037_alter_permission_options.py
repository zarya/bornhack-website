# Generated by Django 4.2.16 on 2024-09-23 06:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('camps', '0036_camp_economy_team'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='permission',
            options={'default_permissions': (), 'managed': False, 'permissions': (('backoffice_permission', 'BackOffice access'), ('badgeteam_permission', 'Badge Team permissions set'), ('barteam_permission', 'Bar Team permissions set'), ('certteam_permission', 'CERT Team permissions set'), ('constructionteam_permission', 'Construction Team permissions set'), ('contentteam_permission', 'Content Team permissions set'), ('economyteam_permission', 'Economy Team permissions set'), ('foodareateam_permission', 'Foodarea Team permissions set'), ('gameteam_permission', 'Game Team permissions set'), ('infoteam_permission', 'Info Team permissions set'), ('lightteam_permission', 'Light Team permissions set'), ('logisticsteam_permission', 'Logistics Team permissions set'), ('metricsteam_permission', 'Metrics Team permissions set'), ('nocteam_permission', 'NOC Team permissions set'), ('orgateam_permission', 'Orga Team permissions set'), ('pocteam_permission', 'POC Team permissions set'), ('prteam_permission', 'PR Team permissions set'), ('phototeam_permission', 'Photo Team permissions set'), ('powerteam_permission', 'Power Team permissions set'), ('rocteam_permission', 'ROC Team permissions set'), ('sanitationteam_permission', 'Sanitation Team permissions set'), ('shuttleteam_permission', 'Shuttle Team permissions set'), ('sponsorsteam_permission', 'Sponsors Team permissions set'), ('sysadminteam_permission', 'Sysadmin Team permissions set'), ('videoteam_permission', 'Video Team permissions set'), ('websiteteam_permission', 'Website Team permissions set'), ('wellnessteam_permission', 'Wellness Team permissions set'), ('expense_create_permission', 'Expense Create permission'), ('revenue_create_permission', 'Revenue Create permission'), ('gisteam_permission', 'GIS Team permission set'), ('team_gis_permission', 'Permission to modify team GIS data'))},
        ),
    ]
