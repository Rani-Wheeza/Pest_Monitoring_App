from rest_framework import serializers, status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User


class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "role", "postcode", "district",
                  "consent_to_updates"]
        read_only_fields = ["id", "username", "email", "role"]


class MeView(APIView):
    """GET/PATCH /api/me/ - the signed-in user's profile."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(MeSerializer(request.user).data)

    def patch(self, request):
        serializer = MeSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class LoginView(APIView):
    """POST /api/login/ - swap a username and password for an API token (US-01, replaces Entra ID)."""

    # No session or CSRF checks here: the token returned is the only thing the Angular app keeps
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        # DRF's serializer checks the password and rejects inactive accounts with a 400
        serializer = AuthTokenSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user": MeSerializer(user).data})


class LogoutView(APIView):
    """POST /api/logout/ - delete the user's token so it can't be used again."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
