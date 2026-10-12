"""API tests for US-04 (view map) and US-05 (filter map)."""
from datetime import timedelta

import pytest
from django.utils import timezone

from sightings.models import PestSighting

pytestmark = pytest.mark.django_db


def _submit(client, payload, **changes):
    payload = {**payload, **changes}
    return client.post("/api/sightings/", payload, format="json").json()["id"]


def _confirm(client, sid, priority="High"):
    client.patch(f"/api/sightings/{sid}/review/", {"decision": "confirm", "priority": priority}, format="json")


def test_public_map_shows_only_reviewed_sightings(client_for, anon_client, resident, worker, sighting_payload):
    reviewed = _submit(client_for(resident), sighting_payload)
    _submit(client_for(resident), sighting_payload)  # still awaiting review
    _confirm(client_for(worker), reviewed)

    features = anon_client.get("/api/map/").json()["features"]
    assert [f["properties"]["id"] for f in features] == [reviewed]
    assert features[0]["properties"]["heat_weight"] == 3


def test_public_map_rounds_coordinates(client_for, anon_client, resident, worker, sighting_payload):
    sid = _submit(client_for(resident), sighting_payload)
    _confirm(client_for(worker), sid)
    lon, lat = anon_client.get("/api/map/").json()["features"][0]["geometry"]["coordinates"]
    assert (lon, lat) == (-9.703, 52.271)


def test_worker_map_includes_unreviewed_with_exact_position(client_for, resident, worker, sighting_payload):
    _submit(client_for(resident), sighting_payload)
    features = client_for(worker).get("/api/map/").json()["features"]
    assert len(features) == 1
    assert features[0]["geometry"]["coordinates"] == [-9.70261, 52.27135]


def test_rejected_sightings_never_on_map(client_for, resident, worker, sighting_payload):
    sid = _submit(client_for(resident), sighting_payload)
    client_for(worker).patch(f"/api/sightings/{sid}/review/", {"decision": "reject", "reason": "Fake"}, format="json")
    assert client_for(worker).get("/api/map/").json()["features"] == []


def test_filter_by_family_and_species(client_for, resident, worker, sighting_payload, pigeon):
    rat_id = _submit(client_for(resident), sighting_payload)
    pigeon_id = _submit(client_for(resident), sighting_payload, species_id=pigeon.pk)
    w = client_for(worker)

    by_family = w.get("/api/map/?family=muridae").json()["features"]
    assert [f["properties"]["id"] for f in by_family] == [rat_id]

    by_species = w.get(f"/api/map/?species_id={pigeon.pk}").json()["features"]
    assert [f["properties"]["id"] for f in by_species] == [pigeon_id]

    assert len(w.get("/api/map/").json()["features"]) == 2  # back to all sightings


def test_filter_by_bbox(client_for, resident, worker, sighting_payload):
    _submit(client_for(resident), sighting_payload)
    w = client_for(worker)
    assert len(w.get("/api/map/?bbox=-9.8,52.2,-9.6,52.4").json()["features"]) == 1
    assert len(w.get("/api/map/?bbox=-8.6,51.8,-8.3,52.0").json()["features"]) == 0


def test_bad_bbox_is_400(anon_client):
    response = anon_client.get("/api/map/?bbox=1,2,3")
    assert response.status_code == 400
    assert "bbox" in response.json()["errors"]


def test_old_sightings_hidden_by_days_filter(client_for, resident, worker, sighting_payload):
    sid = _submit(client_for(resident), sighting_payload)
    PestSighting.objects.filter(pk=sid).update(observed_at=timezone.now() - timedelta(days=100))
    w = client_for(worker)
    assert w.get("/api/map/?days=30").json()["features"] == []   # default view: last 30 days
    assert len(w.get("/api/map/?days=365").json()["features"]) == 1
