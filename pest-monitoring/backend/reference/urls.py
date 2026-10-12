from django.urls import path

from . import views

urlpatterns = [
    path("species/", views.SpeciesListView.as_view(), name="species-list"),
    path("tags/", views.TagListView.as_view(), name="tag-list"),
    path("districts/", views.DistrictListView.as_view(), name="district-list"),
]
