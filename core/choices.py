"""Choices shared by several EcoTeams modules."""
from django.db import models


class EcoCategory(models.TextChoices):
    TRANSPORT = 'transport', 'Transport'
    RECYCLING = 'recycling', 'Recyclage'
    ENERGY = 'energy', 'Énergie'
    WATER = 'water', 'Eau'
    CONSUMPTION = 'consumption', 'Consommation responsable'
    FOOD = 'food', 'Alimentation et anti-gaspillage'


CATEGORY_ICONS = {
    EcoCategory.TRANSPORT: 'bike',
    EcoCategory.RECYCLING: 'recycle',
    EcoCategory.ENERGY: 'zap',
    EcoCategory.WATER: 'droplet',
    EcoCategory.CONSUMPTION: 'shopping-bag',
    EcoCategory.FOOD: 'apple',
}


class Audience(models.TextChoices):
    ALL = 'all', 'Tout public'
    STUDENTS = 'students', 'Étudiants et jeunes'
    EMPLOYEES = 'employees', 'Salariés et entreprises'
    ASSOCIATIONS = 'associations', 'Associations et collectifs'
