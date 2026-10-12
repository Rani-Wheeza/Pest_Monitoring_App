"""Shared pytest fixtures for the Django API tests."""
import io
from datetime import timedelta

import pytest
from django.core.cache import cache
from django.utils import timezone
from PIL import Image
from rest_framework.test import APIClient

from accounts.models import User
from reference.models import District, PestSpecies, Tag


@pytest.fixture(autouse=True)
def _isolated(settings, tmp_path):
    """Each test gets its own media folder and a fresh rate-limit counter."""
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.ENTRA_TENANT_ID = ""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def district(db):
    return District.objects.create(name="Riverside", centre_lat=52.2713, centre_lon=-9.7026)


@pytest.fixture
def other_district(db):
    return District.objects.create(name="Oakfield", centre_lat=52.10, centre_lon=-9.50)


@pytest.fixture
def rat(db):
    return PestSpecies.objects.create(common_name="Brown rat", category="Rodent", family="Muridae",
                                      genus="Rattus", peak_season_start_month=9, peak_season_end_month=3)


@pytest.fixture
def pigeon(db):
    return PestSpecies.objects.create(common_name="Feral pigeon", category="Avian", family="Columbidae",
                                      genus="Columba")


@pytest.fixture
def tags(db):
    return [Tag.objects.create(name="Near food"), Tag.objects.create(name="Outdoors")]


@pytest.fixture
def resident(db, district):
    return User.objects.create_user("aisha", email="aisha@example.com", role="User",
                                    district=district, consent_to_updates=True)


@pytest.fixture
def other_resident(db, district):
    return User.objects.create_user("owen", email="owen@example.com", role="User", district=district)


@pytest.fixture
def worker(db):
    return User.objects.create_user("maya", email="maya@example.org", role="Worker")


@pytest.fixture
def anon_client():
    return APIClient()


@pytest.fixture
def client_for():
    def make(user):
        client = APIClient()
        client.force_authenticate(user)
        return client
    return make


@pytest.fixture
def sighting_payload(rat, tags):
    return {
        "species_id": rat.pk,
        "count": "2-5",
        "description": "Several rats near the bins behind the community centre.",
        "latitude": 52.27135,
        "longitude": -9.70261,
        "location_accuracy_m": 12,
        "street_or_landmark": "Bins behind Riverside Community Centre",
        "suburb_or_postcode": "Riverside, 3021",
        "observed_at": (timezone.now() - timedelta(hours=2)).isoformat(),
        "tag_ids": [t.pk for t in tags],
        "reporter_confirmed": True,
    }


def image_bytes(fmt="PNG", exif=False, mode="RGB"):
    image = Image.new(mode, (20, 20), color=(10, 120, 60) if mode == "RGB" else 1)
    out = io.BytesIO()
    kwargs = {}
    if exif:
        data = Image.Exif()
        data[0x010F] = "PhoneMaker"
        kwargs["exif"] = data.tobytes()
    image.save(out, format=fmt, **kwargs)
    return out.getvalue()
