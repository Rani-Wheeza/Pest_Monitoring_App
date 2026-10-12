from rest_framework import generics
from rest_framework.permissions import AllowAny

from .models import District, PestSpecies, Tag
from .serializers import DistrictSerializer, PestSpeciesSerializer, TagSerializer


class SpeciesListView(generics.ListAPIView):
    """GET /api/species/ - choices for the report form and the map filter."""

    permission_classes = [AllowAny]
    serializer_class = PestSpeciesSerializer
    pagination_class = None
    queryset = PestSpecies.objects.filter(is_active=True)


class TagListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = TagSerializer
    pagination_class = None
    queryset = Tag.objects.all()


class DistrictListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = DistrictSerializer
    pagination_class = None
    queryset = District.objects.all()
