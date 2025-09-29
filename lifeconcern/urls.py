from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Authentication (login/logout)
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    
    # Logout should use a POST request for CSRF safety
    path('logout/', auth_views.LogoutView.as_view(template_name='core/logged_out.html'), name='logout'),

    # Built-in auth URLs (password reset, etc.)
    path('accounts/', include('django.contrib.auth.urls')),

    # Custom accounts app URLs
    path('accounts/', include('accounts.urls')),

    # Core app URLs
    path('', include('core.urls')),  # Root path, e.g., /dashboard/ comes from core.urls
]
