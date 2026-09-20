import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG = os.getenv('POL_DEBUG','0') == '1'
SECRET_KEY = os.getenv('POL_SECRET_KEY','')
if not SECRET_KEY:
    if DEBUG: SECRET_KEY = 'local-development-only-do-not-use-in-production-pol'
    else: raise RuntimeError('Set POL_SECRET_KEY before starting the production server.')
ALLOWED_HOSTS = [x.strip() for x in os.getenv('POL_ALLOWED_HOSTS','localhost,127.0.0.1,testserver').split(',') if x.strip()]
CSRF_TRUSTED_ORIGINS = [x for x in os.getenv('POL_CSRF_ORIGINS','').split(',') if x]
INSTALLED_APPS = ['django.contrib.admin','django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles','academy']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware','whitenoise.middleware.WhiteNoiseMiddleware','django.contrib.sessions.middleware.SessionMiddleware','django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware','django.contrib.auth.middleware.AuthenticationMiddleware','django.contrib.messages.middleware.MessageMiddleware','django.middleware.clickjacking.XFrameOptionsMiddleware']
ROOT_URLCONF = 'config.urls'
TEMPLATES = [{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[BASE_DIR/'templates'],'APP_DIRS':True,'OPTIONS':{'context_processors':['django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages','academy.context.common']}}]
WSGI_APPLICATION = 'config.wsgi.application'
DATABASES = {'default':{'ENGINE':'django.db.backends.sqlite3','NAME':os.getenv('POL_DB_PATH',str(BASE_DIR/'data/pol.sqlite3')),'OPTIONS':{'timeout':20}}}
AUTH_USER_MODEL = 'academy.User'
AUTH_PASSWORD_VALIDATORS = [{'NAME':'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},{'NAME':'django.contrib.auth.password_validation.MinimumLengthValidator','OPTIONS':{'min_length':10}},{'NAME':'django.contrib.auth.password_validation.CommonPasswordValidator'},{'NAME':'django.contrib.auth.password_validation.NumericPasswordValidator'}]
LANGUAGE_CODE = 'fa'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR/'static']
STATIC_ROOT = BASE_DIR/'staticfiles'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 28800
SESSION_SAVE_EVERY_REQUEST = True
SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
if os.getenv('POL_TRUST_PROXY','0') == '1': SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO','https')
DATA_UPLOAD_MAX_MEMORY_SIZE = 1048576
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID','')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET','')
ZARINPAL_MERCHANT_ID = os.getenv('ZARINPAL_MERCHANT_ID','')
PUBLIC_BASE_URL = os.getenv('POL_PUBLIC_BASE_URL','http://127.0.0.1:8000').rstrip('/')
POL_DEMO = os.getenv('POL_DEMO','0') == '1'
POL_SITE_ORIGIN = os.getenv('POL_SITE_ORIGIN','').rstrip('/')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY','')
OPENAI_MODEL = os.getenv('OPENAI_MODEL','')
if not DEBUG and (len(SECRET_KEY)<50 or 'REPLACE_WITH' in SECRET_KEY):
    raise RuntimeError('Production requires a new random POL_SECRET_KEY with at least 50 characters.')

USE_THOUSAND_SEPARATOR = True
