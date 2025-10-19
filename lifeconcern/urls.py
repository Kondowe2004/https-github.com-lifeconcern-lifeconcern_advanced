from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    # -------------------- Admin --------------------
    path('admin/', admin.site.urls),

    # -------------------- Authentication --------------------
    # Login view with custom template
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    
    # Logout view with POST request and custom template
    path('logout/', auth_views.LogoutView.as_view(template_name='registration/logged_out.html'), name='logout'),

    # Include built-in auth URLs for password reset, password change, etc.
    path('accounts/', include('django.contrib.auth.urls')),

    # Include custom accounts app URLs
    path('accounts/', include('accounts.urls')),

    # -------------------- Core app URLs --------------------
    # All dashboard, projects, reports, donors, facilities, service worker handled here
    path('', include('core.urls')),  # Root path
]
