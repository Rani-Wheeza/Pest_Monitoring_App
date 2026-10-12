from rest_framework import serializers

from .models import District, PestSpecies, Tag


class PestSpeciesSerializer(serializers.ModelSerializer):
    class Meta:
        model = PestSpecies
        fields = ["id", "common_name", "scientific_name", "category", "family", "genus", "is_invasive"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ["id", "name"]
