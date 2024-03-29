from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("user/", include("user_control.urls")),
    path("message/", include("message.urls")),
    path("chat/", include("chatapp.urls")),
]
