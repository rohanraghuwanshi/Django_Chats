import random
import re
import string
from datetime import datetime, timedelta

import jwt
from django.conf import settings
from django.contrib.auth import authenticate
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.pagination import PageNumberPagination

from .authentication import Authentication
from .models import JWT, CustomUser
from .serializers import (
    LoginSerializer,
    RefreshSerializer,
    RegisterSerializer,
    UserProfile,
    UserProfileSerializer,
)


def get_random(length):
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


def get_access_token(payload):
    return jwt.encode(
        {"exp": datetime.now() + timedelta(minutes=5), **payload},
        settings.SECRET_KEY,
        algorithm="HS256",
    )


def get_refresh_token():
    return jwt.encode(
        {"exp": datetime.now() + timedelta(days=365), "data": get_random(10)},
        settings.SECRET_KEY,
        algorithm="HS256",
    )


class LoginView(APIView):
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )

        if not user:
            return Response({"error": "Invalid username or password"}, status="400")

        JWT.objects.filter(user_id=user.id).delete()

        access = get_access_token({"user_id": user.id})
        refresh = get_refresh_token()

        new_jwt = JWT.objects.create(
            user_id=user.id,
            access=jwt.decode(access, settings.SECRET_KEY, algorithms="HS256"),
            refresh=jwt.decode(refresh, settings.SECRET_KEY,
                               algorithms="HS256"),
        )

        new_jwt.save()

        return Response({"access": access, "refresh": refresh})


class RegisterView(APIView):
    serializer_class = RegisterSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        CustomUser.objects._create_user(**serializer.validated_data)

        return Response({"success": "User created."})


class RefreshView(APIView):
    serializer_class = RefreshSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh = serializer.validated_data["refresh"]
        refresh = jwt.decode(refresh, settings.SECRET_KEY, algorithms="HS256")

        try:
            active_jwt = JWT.objects.get(refresh=refresh)
        except JWT.DoesNotExist:
            return Response({"error": "refresh token not found"}, status="400")

        if not Authentication.verify_token(serializer.validated_data["refresh"]):
            return Response({"error": "Token is invalid or has expired"})

        access = get_access_token({"user_id": active_jwt.user.id})
        refresh = get_refresh_token()

        active_jwt.access = jwt.decode(
            access, settings.SECRET_KEY, algorithms="HS256")
        active_jwt.refresh = jwt.decode(
            refresh, settings.SECRET_KEY, algorithms="HS256"
        )
        active_jwt.save()

        return Response({"access": access, "refresh": refresh})


class UserProfileView(ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        data = self.request.query_params.dict()
        keyword = data.get("keyword", None)

        if keyword:
            search_fields = ("user__username", "first_name", "last_name")
            query = self.get_query(keyword, search_fields)
            return self.queryset.filter(query).distinct()

        return self.queryset

    @staticmethod
    def get_query(query_string, search_fields):

        query = None
        terms = UserProfileView.normalize_query(query_string)

        for term in terms:
            or_query = None
            for field_name in search_fields:
                q = Q(**{"%s__icontains" % field_name: term})
                if or_query is None:
                    or_query = q
                else:
                    or_query = or_query | q

            if query is None:
                query = or_query
            else:
                query = or_query

        return query

    @staticmethod
    def normalize_query(
        query_string,
        findterms=re.compile(r'"([^"]+)"|(\S+)').findall,
        normspace=re.compile(r"\s{2,}").sub,
    ):
        return [normspace(" ", (t[0] or t[1]).strip()) for t in findterms(query_string)]
