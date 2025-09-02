from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Shortcut for /login/ and /logout/
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Auth URLs (accounts/login/, password reset, etc.)
    path('accounts/', include('django.contrib.auth.urls')),

    # Your custom accounts URLs
    path('accounts/', include('accounts.urls')),

    # Core app
    path('', include('core.urls')),
]
