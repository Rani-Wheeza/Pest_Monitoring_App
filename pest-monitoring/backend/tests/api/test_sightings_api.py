"""API tests for US-02 (submit), US-03 (photo) and sighting review."""
import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from sightings.models import PestSighting, SightingStatusHistory
from tests.conftest import image_bytes

pytestmark = pytest.mark.django_db

SUBMIT = "/api/sightings/"


# ---------- US-02 Submit pest sighting ----------

def test_species_list_is_public(anon_client, rat, pigeon):
    response = anon_client.get("/api/species/")
    assert response.status_code == 200
    assert [s["common_name"] for s in response.json()] == ["Brown rat", "Feral pigeon"]


def test_signed_in_user_can_submit(client_for, resident, sighting_payload, district):
    response = client_for(resident).post(SUBMIT, sighting_payload, format="json")
    assert response.status_code == 201, response.json()
    body = response.json()
    assert body["reference"].startswith("PP-")
    assert body["status"] == "AwaitingReview"
    assert body["resident_status"] == "Awaiting review"
    assert body["count_min"] == 2 and body["count_max"] == 5
    assert sorted(body["tags"]) == ["Near food", "Outdoors"]
    assert "upload_token" not in body

    sighting = PestSighting.objects.get(pk=body["id"])
    assert sighting.reporter == resident
    assert sighting.district == district  # nearest district centre to the pin
    assert SightingStatusHistory.objects.filter(sighting=sighting, to_status="AwaitingReview").exists()


def test_anonymous_submit_needs_contact_email(anon_client, sighting_payload):
    response = anon_client.post(SUBMIT, sighting_payload, format="json")
    assert response.status_code == 400
    assert "contact_email" in response.json()["errors"]


def test_anonymous_submit_with_email_gets_upload_token(anon_client, sighting_payload):
    sighting_payload["contact_email"] = "someone@example.com"
    response = anon_client.post(SUBMIT, sighting_payload, format="json")
    assert response.status_code == 201
    assert response.json()["upload_token"]
    assert PestSighting.objects.get().reporter is None


def test_all_missing_fields_reported_together(client_for, resident):
    response = client_for(resident).post(SUBMIT, {}, format="json")
    assert response.status_code == 400
    errors = response.json()["errors"]
    for field in ["species_id", "count", "description", "location", "street_or_landmark",
                  "suburb_or_postcode", "reporter_confirmed"]:
        assert field in errors, field


def test_unknown_species_rejected(client_for, resident, sighting_payload):
    sighting_payload["species_id"] = 9999
    response = client_for(resident).post(SUBMIT, sighting_payload, format="json")
    assert response.status_code == 400
    assert "species_id" in response.json()["errors"]


def test_bad_count_format_rejected(client_for, resident, sighting_payload):
    sighting_payload["count"] = "lots"
    response = client_for(resident).post(SUBMIT, sighting_payload, format="json")
    assert response.status_code == 400
    assert "count" in response.json()["errors"]


def test_future_sighting_rejected(client_for, resident, sighting_payload):
    sighting_payload["observed_at"] = "2099-01-01T10:00:00Z"
    response = client_for(resident).post(SUBMIT, sighting_payload, format="json")
    assert response.status_code == 400
    assert "observed_at" in response.json()["errors"]


def test_my_sightings_only_shows_mine(client_for, resident, other_resident, sighting_payload):
    client_for(resident).post(SUBMIT, sighting_payload, format="json")
    client_for(other_resident).post(SUBMIT, sighting_payload, format="json")
    response = client_for(resident).get("/api/sightings/mine/")
    assert response.status_code == 200
    assert response.json()["count"] == 1


def test_my_sightings_requires_sign_in(anon_client):
    assert anon_client.get("/api/sightings/mine/").status_code in (401, 403)


def test_detail_visible_to_owner_and_worker_only(client_for, resident, other_resident, worker, sighting_payload):
    sid = client_for(resident).post(SUBMIT, sighting_payload, format="json").json()["id"]
    assert client_for(resident).get(f"/api/sightings/{sid}/").status_code == 200
    assert client_for(worker).get(f"/api/sightings/{sid}/").status_code == 200
    assert client_for(other_resident).get(f"/api/sightings/{sid}/").status_code == 403
    assert client_for(worker).get("/api/sightings/99999/").status_code == 404


# ---------- US-03 Attach a photo ----------

def _submit(client, payload):
    return client.post(SUBMIT, payload, format="json").json()


def _upload(client, sid, data, name="photo.png", content_type="image/png", **headers):
    file = SimpleUploadedFile(name, data, content_type=content_type)
    return client.post(f"/api/sightings/{sid}/photo/", {"photo": file}, format="multipart", **headers)


def test_owner_can_attach_png(client_for, resident, sighting_payload):
    client = client_for(resident)
    sid = _submit(client, sighting_payload)["id"]
    response = _upload(client, sid, image_bytes("PNG"))
    assert response.status_code == 201, response.json()
    assert response.json()["content_type"] == "image/png"
    assert client.get(f"/api/sightings/{sid}/").json()["photos"][0]["media_type"] == "Image"


def test_stored_photo_has_no_exif(client_for, resident, sighting_payload):
    client = client_for(resident)
    sid = _submit(client, sighting_payload)["id"]
    _upload(client, sid, image_bytes("JPEG", exif=True), name="p.jpg", content_type="image/jpeg")
    media = PestSighting.objects.get(pk=sid).media.get()
    with media.file.open("rb") as stored:
        assert len(Image.open(io.BytesIO(stored.read())).getexif()) == 0


def test_gif_rejected(client_for, resident, sighting_payload):
    client = client_for(resident)
    sid = _submit(client, sighting_payload)["id"]
    response = _upload(client, sid, image_bytes("GIF", mode="P"), name="a.gif", content_type="image/gif")
    assert response.status_code == 400
    assert "photo" in response.json()["errors"]


def test_other_user_cannot_attach_photo(client_for, resident, other_resident, sighting_payload):
    sid = _submit(client_for(resident), sighting_payload)["id"]
    assert _upload(client_for(other_resident), sid, image_bytes()).status_code == 403


def test_anonymous_reporter_uses_upload_token(anon_client, sighting_payload):
    sighting_payload["contact_email"] = "someone@example.com"
    body = _submit(anon_client, sighting_payload)
    assert _upload(anon_client, body["id"], image_bytes()).status_code == 403
    ok = _upload(anon_client, body["id"], image_bytes(), HTTP_X_UPLOAD_TOKEN=body["upload_token"])
    assert ok.status_code == 201


def test_at_most_three_photos(client_for, resident, sighting_payload):
    client = client_for(resident)
    sid = _submit(client, sighting_payload)["id"]
    for _ in range(3):
        assert _upload(client, sid, image_bytes()).status_code == 201
    assert _upload(client, sid, image_bytes()).status_code == 400


def test_missing_file_rejected(client_for, resident, sighting_payload):
    client = client_for(resident)
    sid = _submit(client, sighting_payload)["id"]
    response = client.post(f"/api/sightings/{sid}/photo/", {}, format="multipart")
    assert response.status_code == 400


# ---------- Review by a worker ----------

def test_worker_confirms_with_priority(client_for, resident, worker, sighting_payload):
    sid = _submit(client_for(resident), sighting_payload)["id"]
    response = client_for(worker).patch(f"/api/sightings/{sid}/review/",
                                        {"decision": "confirm", "priority": "High"}, format="json")
    assert response.status_code == 200, response.json()
    assert response.json()["status"] == "Confirmed"
    assert response.json()["priority"] == "High"
    assert SightingStatusHistory.objects.filter(sighting_id=sid, to_status="Confirmed",
                                                changed_by=worker).exists()


def test_confirm_needs_priority(client_for, resident, worker, sighting_payload):
    sid = _submit(client_for(resident), sighting_payload)["id"]
    response = client_for(worker).patch(f"/api/sightings/{sid}/review/", {"decision": "confirm"}, format="json")
    assert response.status_code == 400
    assert "priority" in response.json()["errors"]


def test_reject_needs_reason(client_for, resident, worker, sighting_payload):
    sid = _submit(client_for(resident), sighting_payload)["id"]
    url = f"/api/sightings/{sid}/review/"
    assert client_for(worker).patch(url, {"decision": "reject"}, format="json").status_code == 400
    ok = client_for(worker).patch(url, {"decision": "reject", "reason": "Duplicate of PP-1"}, format="json")
    assert ok.json()["status"] == "Rejected"


def test_cannot_review_twice(client_for, resident, worker, sighting_payload):
    sid = _submit(client_for(resident), sighting_payload)["id"]
    url = f"/api/sightings/{sid}/review/"
    client_for(worker).patch(url, {"decision": "confirm", "priority": "Low"}, format="json")
    assert client_for(worker).patch(url, {"decision": "reject", "reason": "x"}, format="json").status_code == 400


def test_resident_cannot_review(client_for, resident, sighting_payload):
    sid = _submit(client_for(resident), sighting_payload)["id"]
    response = client_for(resident).patch(f"/api/sightings/{sid}/review/",
                                          {"decision": "confirm", "priority": "High"}, format="json")
    assert response.status_code == 403


def test_worker_lists_all_by_status(client_for, resident, worker, sighting_payload):
    _submit(client_for(resident), sighting_payload)
    response = client_for(worker).get("/api/sightings/all/?status=AwaitingReview")
    assert response.status_code == 200 and response.json()["count"] == 1
    assert client_for(resident).get("/api/sightings/all/").status_code == 403
