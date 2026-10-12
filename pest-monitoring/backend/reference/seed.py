"""Starter reference data (matches Task 5 schema.sql). Safe to run more than once."""
from .models import District, PestSpecies, Tag

DISTRICTS = ["Riverside", "Oakfield", "Northgate", "Willow Court"]

SPECIES = [
    # common name, scientific name, category, family, genus, invasive, season start, season end
    ("Brown rat", "Rattus norvegicus", "Rodent", "Muridae", "Rattus", False, 9, 3),
    ("Black rat", "Rattus rattus", "Rodent", "Muridae", "Rattus", False, 9, 3),
    ("House mouse", "Mus musculus", "Rodent", "Muridae", "Mus", False, 10, 2),
    ("Grey squirrel", "Sciurus carolinensis", "Rodent", "Sciuridae", "Sciurus", True, None, None),
    ("Feral pigeon", "Columba livia", "Avian", "Columbidae", "Columba", False, None, None),
    ("Herring gull", "Larus argentatus", "Avian", "Laridae", "Larus", False, 4, 8),
]

TAGS = ["Near food", "Outdoors", "Indoor", "Multiple pests", "Property damage", "Recurring"]


def seed_reference_data() -> dict:
    created = {"districts": 0, "species": 0, "tags": 0}
    for name in DISTRICTS:
        created["districts"] += District.objects.get_or_create(name=name)[1]
    for common, sci, cat, family, genus, invasive, start, end in SPECIES:
        created["species"] += PestSpecies.objects.get_or_create(
            common_name=common,
            defaults=dict(scientific_name=sci, category=cat, family=family, genus=genus,
                          is_invasive=invasive, peak_season_start_month=start, peak_season_end_month=end),
        )[1]
    for name in TAGS:
        created["tags"] += Tag.objects.get_or_create(name=name)[1]
    return created
