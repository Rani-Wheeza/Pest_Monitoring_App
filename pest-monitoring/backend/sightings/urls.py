from django.urls import path

from . import views

urlpatterns = [
    path("sightings/", views.SightingSubmitView.as_view(), name="sighting-submit"),
    path("sightings/mine/", views.MySightingsView.as_view(), name="sighting-mine"),
    path("sightings/all/", views.AllSightingsView.as_view(), name="sighting-all"),
    path("sightings/<int:sighting_id>/", views.SightingDetailView.as_view(), name="sighting-detail"),
    path("sightings/<int:sighting_id>/photo/", views.SightingPhotoView.as_view(), name="sighting-photo"),
    path("sightings/<int:sighting_id>/review/", views.SightingReviewView.as_view(), name="sighting-review"),
    path("map/", views.MapView.as_view(), name="map"),
]
