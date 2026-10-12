"""Lookup tables: districts, pest species and tags (Task 5, section A)."""
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class District(models.Model):
    name = models.CharField(max_length=100, unique=True)
    postcode_prefix = models.CharField(max_length=10, blank=True)
    centre_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    centre_lon = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        db_table = "District"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class PestSpecies(models.Model):
    class Category(models.TextChoices):
        RODENT = "Rodent"
        AVIAN = "Avian"
        INSECT = "Insect"
        OTHER = "Other"

    common_name = models.CharField(max_length=100, unique=True)
    scientific_name = models.CharField(max_length=150, blank=True)
    category = models.CharField(max_length=20, choices=Category.choices)
    family = models.CharField(max_length=100, blank=True)
    genus = models.CharField(max_length=100, blank=True)
    is_invasive = models.BooleanField(default=False)
    peak_season_start_month = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(12)])
    peak_season_end_month = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(12)])
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "PestSpecies"
        ordering = ["common_name"]
        verbose_name_plural = "pest species"

    def __str__(self) -> str:
        return self.common_name


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = "Tag"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
