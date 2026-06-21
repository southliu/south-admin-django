import yaml
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

_config_path = BASE_DIR / "config.yaml"
with open(_config_path, "r", encoding="utf-8") as f:
    _config = yaml.safe_load(f)

_db = _config["database"]
_jwt = _config["jwt"]

SECRET_KEY = _jwt["secret_key"]

DEBUG = True

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'systems.user',
    'systems.role',
    'systems.menu',
    'systems.permission',
    'systems.log',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'middleware.auth.AuthMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'middleware.log.LogMiddleware',
]

ROOT_URLCONF = 'south_admin_django.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'south_admin_django.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': _db["name"],
        'USER': _db["user"],
        'PASSWORD': _db["password"],
        'HOST': _db["host"],
        'PORT': str(_db["port"]),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = False

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

JWT_SECRET_KEY = _jwt["secret_key"]
JWT_ALGORITHM = _jwt["algorithm"]
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = _jwt["access_token_expire_minutes"]
