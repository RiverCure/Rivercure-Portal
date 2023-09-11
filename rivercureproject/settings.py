from dotenv import load_dotenv
import os

load_dotenv()

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if os.name == 'nt':
    import platform
    OSGEO4W = r"C:\OSGeo4W"
    if '64' in platform.architecture()[0]:
        OSGEO4W += "64"
    assert os.path.isdir(OSGEO4W), "Directory does not exist: " + OSGEO4W
    os.environ['OSGEO4W_ROOT'] = OSGEO4W
    os.environ['GDAL_DATA'] = OSGEO4W + r"\share\gdal"
    os.environ['PROJ_LIB'] = OSGEO4W + r"\share\proj"
    os.environ['PATH'] = OSGEO4W + r"\bin;" + os.environ['PATH']

# GDAL_LIBRARY_PATH = '/opt/homebrew/opt/gdal/lib/libgdal.dylib'
# GEOS_LIBRARY_PATH = '/opt/homebrew/opt/geos/lib/libgeos_c.dylib'
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '^s&4uf&m0lgol2@%+-+7714k2t)wexo3j*b98dl3w_d-$z-e@b'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = (os.getenv('DEBUG', 'False') == 'True')

FILES_BASE_PATH = os.getenv('FILES_BASE_PATH', BASE_DIR)

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '192.168.139.2',
    'rivercure.inesc-id.pt'
]  # Must be changed to allow host in production

# Application definition
INSTALLED_APPS = [
    'notifications',
    'raster',
    'leaflet',
    'organization.apps.OrganizationConfig',
    'sensors.apps.SensorsConfig',
    'rivercureportal.apps.RivercureportalConfig',
    'users.apps.UsersConfig',
    'context.apps.ContextConfig',
    'crispy_forms',
    'rest_framework',
    'corsheaders',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'django_filters',
    'bootstrapform',
    'django_celery_results',
    'celery_progress'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'rivercureproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'rivercureproject.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('DATABASE_NAME', ''),
        'USER': os.getenv('DATABASE_USER', ''),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', ''),
        'HOST': os.getenv('DATABASE_HOST', ''),
        'PORT': os.getenv('DATABASE_PORT', ''),
        'TEST': {
            'NAME': 'rcp_test_db',
            'TEMPLATE': os.getenv('DATABASE_NAME', '')
        },
    }
}

AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.ModelBackend']
# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Lisbon'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Leaftlet configurations
LEAFLET_CONFIG = {
    'DEFAULT_CENTER': (38.707616, -9.1365),  # Lisbon coordinates
    'DEFAULT_ZOOM': 6,
    'MIN_ZOOM': 3,
    'MAX_ZOOM': 18,
    'RESET_VIEW': False,
    'TILES': [('Satellite', 'https://api.mapbox.com/styles/v1/mapbox/{id}/tiles/512/{z}/{x}/{y}@2x?access_token={accessToken}', {
        'id': 'satellite-streets-v11',
        'accessToken': 'pk.eyJ1Ijoiam9yZ2Vtc21hcnF1ZXMiLCJhIjoiY2tkMHM2cGE0MHExNTJ5bzdudzJkemo2aSJ9.-9GKsDPOItWz1CYx0aq0Iw',
        'attribution': '''&copy <a href="https://www.mapbox.com/about/maps/">Mapbox</a> 
                                &copy <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> 
                                <strong><a href="https://www.mapbox.com/map-feedback/" target="_blank">Improve this map</a></strong>'''
    }),
        ('Contour Lines', 'https://api.mapbox.com/styles/v1/mapbox/{id}/tiles/512/{z}/{x}/{y}@2x?access_token={accessToken}', {
            'id': 'outdoors-v11',
            'accessToken': 'pk.eyJ1Ijoiam9yZ2Vtc21hcnF1ZXMiLCJhIjoiY2tkMHM2cGE0MHExNTJ5bzdudzJkemo2aSJ9.-9GKsDPOItWz1CYx0aq0Iw',
            'attribution': '''&copy <a href="https://www.mapbox.com/about/maps/">Mapbox</a> 
                                &copy <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> 
                                <strong><a href="https://www.mapbox.com/map-feedback/" target="_blank">Improve this map</a></strong>'''
        }),
        ('OpenStreetMaps', 'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
         'attribution': '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMaps</a> contributors'}),
        ('Blank', '', {}),
    ]
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = 'static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'static')


MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

CRISPY_TEMPLATE_PACK = 'bootstrap4'

LOGIN_REDIRECT_URL = 'rivercure-home'
LOGIN_URL = 'login'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_PORT = os.getenv('EMAIL_PORT', '')
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
SERVER_EMAIL = EMAIL_HOST_USER
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

if os.getenv('DEBUG', 'False') == 'True':
    SESSION_COOKIE_AGE = 8000 * 60  # TIME FOR COOKIES TO EXPIRE
    SESSION_EXPIRE_AT_BROWSER_CLOSE = False
else:
    SESSION_COOKIE_AGE = 8 * 60  # TIME FOR COOKIES TO EXPIRE
    SESSION_EXPIRE_AT_BROWSER_CLOSE = True

SESSION_SAVE_EVERY_REQUEST = True

CORS_ORIGIN_ALLOW_ALL = True  # This should be removed enventually

# RASTER_USE_CELERY = True

CELERY_BROKER_URL = 'amqp://guest:guest@localhost:5672//'
CELERY_ACCEPT_CONTENT = ['json', 'pickle']
CELERY_TASK_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Europe/London'
CELERY_RESULT_BACKEND = 'django-db'

GDAL_LIBRARY_PATH = os.getenv('GDAL_LIBRARY_PATH')
GEOS_LIBRARY_PATH = os.getenv('GEOS_LIBRARY_PATH')
