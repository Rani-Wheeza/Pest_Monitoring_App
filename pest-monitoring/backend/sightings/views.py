"""HTTP endpoints for sightings. Views stay thin: parse, call a service, respond."""
from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsWorker
from domain.geo import parse_bbox

from . import repositories as repo
from . import services
from .exceptions import DomainValidationError, NotAllowedError
from .serializers import (
    MapQuerySerializer,
    ReviewSerializer,
    SightingCreateSerializer,
    SightingMediaSerializer,
    SightingSerializer,
)


def _error_response(exc: Exception) -> Response:
    if isinstance(exc, DomainValidationError):
        return Response({"errors": exc.as_dict()}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)


def _get_or_404(sighting_id: int):
    sighting = repo.get_sighting(sighting_id)
    if sighting is None:
        return None, Response({"detail": "Sighting not found."}, status=status.HTTP_404_NOT_FOUND)
    return sighting, None


class SightingSubmitView(APIView):
    """POST /api/sightings/ - submit a sighting (signed in, or anonymous with an email)."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SightingCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        user = request.user if request.user.is_authenticated else None
        try:
            sighting = services.submit_sighting(serializer.to_domain(is_anonymous=user is None),
                                                serializer.validated_data["tag_ids"], reporter=user)
        except DomainValidationError as exc:
            return _error_response(exc)
        body = SightingSerializer(sighting, context={"request": request}).data
        if user is None:
            body["upload_token"] = services.make_upload_token(sighting)
        return Response(body, status=status.HTTP_201_CREATED)


class MySightingsView(generics.ListAPIView):
    """GET /api/sightings/mine/ - the signed-in user's reports (resident dashboard)."""

    permission_classes = [IsAuthenticated]
    serializer_class = SightingSerializer

    def get_queryset(self):
        return repo.sightings_for_reporter(self.request.user)


class AllSightingsView(generics.ListAPIView):
    """GET /api/sightings/all/?status=&priority= - every report (workers only)."""

    permission_classes = [IsWorker]
    serializer_class = SightingSerializer

    def get_queryset(self):
        return repo.all_sightings(self.request.query_params.get("status"),
                                  self.request.query_params.get("priority"))


class SightingDetailView(APIView):
    """GET /api/sightings/<id>/ - one report (its reporter or a worker)."""

    permission_classes = [IsAuthenticated]

    def get(self, request, sighting_id: int):
        sighting, missing = _get_or_404(sighting_id)
        if missing:
            return missing
        if not services.can_view(request.user, sighting):
            return Response({"detail": "Not your sighting."}, status=status.HTTP_403_FORBIDDEN)
        return Response(SightingSerializer(sighting, context={"request": request}).data)


class SightingPhotoView(APIView):
    """POST /api/sightings/<id>/photo/ - multipart field "photo" (JPG/PNG, max 10 MB)."""

    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, sighting_id: int):
        sighting, missing = _get_or_404(sighting_id)
        if missing:
            return missing
        upload = request.FILES.get("photo")
        if upload is None:
            return Response({"errors": {"photo": ["Attach a photo."]}}, status=status.HTTP_400_BAD_REQUEST)
        if upload.size > 10 * 1024 * 1024:
            return Response({"errors": {"photo": ["Photos must be 10 MB or smaller."]}},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            media = services.attach_photo(sighting, upload.read(), user=request.user,
                                          upload_token=request.headers.get("X-Upload-Token"))
        except (DomainValidationError, NotAllowedError) as exc:
            return _error_response(exc)
        return Response(SightingMediaSerializer(media, context={"request": request}).data,
                        status=status.HTTP_201_CREATED)


class SightingReviewView(APIView):
    """PATCH /api/sightings/<id>/review/ - worker confirms or rejects a new sighting."""

    permission_classes = [IsWorker]

    def patch(self, request, sighting_id: int):
        sighting, missing = _get_or_404(sighting_id)
        if missing:
            return missing
        serializer = ReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            sighting = services.review_sighting(sighting, worker=request.user, **serializer.validated_data)
        except (DomainValidationError, NotAllowedError) as exc:
            return _error_response(exc)
        return Response(SightingSerializer(sighting, context={"request": request}).data)


class MapView(APIView):
    """GET /api/map/?species_id=&family=&genus=&days=&bbox= - GeoJSON for Azure Maps."""

    permission_classes = [AllowAny]

    def get(self, request):
        query = MapQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        params = dict(query.validated_data)
        bbox_text = params.pop("bbox", None)
        try:
            bbox = parse_bbox(bbox_text) if bbox_text else None
        except ValueError as exc:
            return Response({"errors": {"bbox": [str(exc)]}}, status=status.HTTP_400_BAD_REQUEST)
        return Response(services.map_features(viewer=request.user, bbox=bbox, **params))
