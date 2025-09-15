from pathlib import Path
import os
import sys

BASE_DIR = Path(__file__).resolve().parent.parent

# -------------------------
# Security settings
# -------------------------
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-lifeconcern-advanced-demo")

DEBUG = os.environ.get("DEBUG", "True") == "True"  # ✅ Fix: True by default in dev

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "lifeconcern.pythonanywhere.com",  # ✅ PythonAnywhere domain
]

CSRF_TRUSTED_ORIGINS = [
    "https://lifeconcern.pythonanywhere.com",
]

# -------------------------
# Installed apps
# -------------------------
INSTALLED_APPS = [
    # Default Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'widget_tweaks',   # ✅ Needed for add_class filter

    # Local apps
    'accounts',
    'core',
]

# -------------------------
# Middleware
# -------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'lifeconcern.urls'

# -------------------------
# Templates
# -------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'lifeconcern.wsgi.application'

# -------------------------
# Database (SQLite cross-platform)
# -------------------------
if sys.platform.startswith("win"):
    # Local Windows
    DB_PATH = BASE_DIR / "db.sqlite3"
else:
    # PythonAnywhere / Linux
    DB_PATH = os.path.expanduser("~/db_backups/db.sqlite3")

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': str(DB_PATH),
    }
}

# -------------------------
# Password validation
# -------------------------
AUTH_PASSWORD_VALIDATORS = []

# -------------------------
# Localization
# -------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Blantyre'
USE_I18N = True
USE_TZ = True

# -------------------------
# Static & Media files
# -------------------------
STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")  # For collectstatic on PythonAnywhere

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# -------------------------
# Default primary key field type
# -------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# -------------------------
# Email settings for alerts
# -------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# Gmail account credentials
EMAIL_HOST_USER = "datamanagementlico@gmail.com"
EMAIL_HOST_PASSWORD = "jbll pppr owrw doap"  # ✅ App password (never use normal password)

# Default sender (use a neutral updates address for classification as 'Updates')
DEFAULT_FROM_EMAIL = "updates@yourdomain.com"
SERVER_EMAIL = DEFAULT_FROM_EMAIL  # Used for error emails from Django

# -------------------------
# Redirects after login/logout
# -------------------------
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = '/login/'
