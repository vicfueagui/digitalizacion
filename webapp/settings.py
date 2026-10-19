import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
WORKSPACE = Path(os.environ['DIGITALIZACION_WEB_WORKSPACE']).resolve()
CONFIG = json.loads((WORKSPACE / '.web' / 'config.json').read_text(encoding='utf-8'))
SECRET_KEY = CONFIG['secret_key']
DEBUG = False
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '[::1]', 'testserver']
ROOT_URLCONF = 'webapp.urls'
INSTALLED_APPS = ['django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions', 'django.contrib.messages', 'webapp']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware', 'webapp.security.LocalOnlyMiddleware',
              'django.contrib.sessions.middleware.SessionMiddleware', 'django.middleware.common.CommonMiddleware',
              'django.middleware.csrf.CsrfViewMiddleware', 'django.contrib.auth.middleware.AuthenticationMiddleware',
              'django.contrib.messages.middleware.MessageMiddleware', 'django.middleware.clickjacking.XFrameOptionsMiddleware']
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': WORKSPACE / '.web' / 'acceso.sqlite3', 'OPTIONS': {'timeout': 20}}}
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': [BASE_DIR / 'webapp' / 'templates'],
              'APP_DIRS': True, 'OPTIONS': {'context_processors': ['django.template.context_processors.request',
              'django.contrib.auth.context_processors.auth', 'django.contrib.messages.context_processors.messages', 'webapp.views.common']}}]
LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'America/Mexico_City'
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = '/acceso/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/acceso/'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 3600
CSRF_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_HTTPONLY = True
SECURE_CONTENT_TYPE_NOSNIFF = True
# Los POST de formularios nativos necesitan conservar el origen propio.
# no-referrer puede convertir Origin en null (Fetch), que CSRF debe rechazar.
# same-origin sigue omitiendo la referencia al navegar a otros sitios.
SECURE_REFERRER_POLICY = 'same-origin'
CSRF_FAILURE_VIEW = 'webapp.security.csrf_failure'
X_FRAME_OPTIONS = 'DENY'
DATA_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024
DATA_UPLOAD_MAX_NUMBER_FILES = 100
FILE_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024
FILE_UPLOAD_TEMP_DIR = str(WORKSPACE / '.web' / 'tmp')
PASSWORD_HASHERS = ['django.contrib.auth.hashers.PBKDF2PasswordHasher']
LOGGING = {'version': 1, 'disable_existing_loggers': False, 'handlers': {'null': {'class': 'logging.NullHandler'}},
           'loggers': {'django.request': {'handlers': ['null'], 'propagate': False},
                       'django.security': {'handlers': ['null'], 'propagate': False}}}
