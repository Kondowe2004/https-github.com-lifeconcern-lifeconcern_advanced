from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Authentication (login/logout)
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Built-in auth URLs (password reset, etc.)
    path('accounts/', include('django.contrib.auth.urls')),

    # Custom accounts app URLs
    path('accounts/', include('accounts.urls')),

    # Core app URLs
    path('', include('core.urls')),  # '' means root path, e.g., /dashboard/ will come from core.urls
]
