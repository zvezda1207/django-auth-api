"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from accounts.views import RegisterView, LoginView, LogoutView, MeView, DeleteMeView
from access_control.views import (
    RoleListCreateView,
    RoleDetailView,
    BusinessElementListCreateView,
    BusinessElementDetailView,
    AccessRoleRuleListCreateView,
    AccessRoleRuleDetailView,
)

from mock_business.views import ProductListCreateView

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/auth/register/', csrf_exempt(RegisterView.as_view())),
    path('api/auth/login/', csrf_exempt(LoginView.as_view())),
    path('api/auth/logout/', csrf_exempt(LogoutView.as_view())),
    path('api/auth/me/', csrf_exempt(MeView.as_view())),
    path('api/auth/me/delete/', csrf_exempt(DeleteMeView.as_view())),

    path('api/products/', csrf_exempt(ProductListCreateView.as_view())),
    
    path('api/admin/roles/', RoleListCreateView.as_view()),
    path('api/admin/roles/<int:pk>/', RoleDetailView.as_view()),

    path('api/admin/elements/', BusinessElementListCreateView.as_view()),
    path('api/admin/elements/<int:pk>/', BusinessElementDetailView.as_view()),

    path('api/admin/access-rules/', AccessRoleRuleListCreateView.as_view()),
    path('api/admin/access-rules/<int:pk>/', AccessRoleRuleDetailView.as_view()),
]
