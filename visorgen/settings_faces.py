"""
Django settings for visorgen project.

Generated by 'django-admin startproject' using Django 1.10.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

import os

######
# Main paths
######

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BASE_DATA_DIR = '/webapps/visorgen/'

######
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/
######

# SECURITY WARNING: keep the secret key used in production secret!
# If you need to generate a new key, see https://pypi.python.org/pypi/django-generate-secret-key/1.0.2
with open( os.path.join(BASE_DIR, '..', 'secret_key_visorgen') )  as f:
    SECRET_KEY = f.read().strip()

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

######
# Application settings
######

# Site prefix, if changed:
#   - keep it with the same pattern '/<prefix>'
#   - needs to be replaced too in your web server proxy configuration file (if used).
SITE_PREFIX = "/vgg_frontend"

# Login URL
LOGIN_URL = SITE_PREFIX + '/login/'

# Allow bulk update of >1K objects
# https://docs.djangoproject.com/en/1.10/ref/settings/#data-upload-max-number-fields
DATA_UPLOAD_MAX_NUMBER_FIELDS = None

######
# Application definition
######

INSTALLED_APPS = [
    'siteroot',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'visorgen.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'visorgen.wsgi.application'


######
# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases
######

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


######
# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators
######

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


######
# Cache settings
# https://docs.djangoproject.com/en/1.10/topics/cache/
######

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}


######
# Session settings
######

SESSION_ENGINE = "django.contrib.sessions.backends.file"

SESSION_EXPIRE_AT_BROWSER_CLOSE = True


######
# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/
######

LANGUAGE_CODE = 'en-uk'

TIME_ZONE = 'GB'

USE_I18N = True

USE_L10N = True

USE_TZ = True


######
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/
######

STATIC_URL = SITE_PREFIX + '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'siteroot', 'static')


######
# Visor web site options
######

VISOR = {
    'title': 'My Visual Search Engine',
    'disable_autocomplete': True,
    'results_per_page' : 50,
    'check_backends_reachable': True,
    'select_roi' : True, # enable only when the selected backend is able to receive ROIs as input
    'enable_viewsel' : True, # enable only when the selected backend is able to return ROIs
    'datasets' : {  # Dictionary of datasets. Only one dataset at a time is supported.
                    # The key-name of the dataset is used to locate subfolders within
                    # the different PATHS used by the controller.

                    'mydataset' : 'Any dataset'
                 },
    'engines' : {

                # Sample backend engine for face search.
                # It support images and text as input.
                'faces' :   { 'full_name' : 'People',
                              'url': '/',
                              'backend_port' : 55302,
                              'imgtools_postproc_module' : 'download_disabled',  # Disable image download before postprocessing
                              'imgtools_style': 'face',
                              'pattern_fname_classifier' : 'dummy', # Not used but cannot be 'None'
                              'can_save_uber_classifier': True,
                              'skip_query_progress': False,
                              'engine_for_similar_search': 'faces'
                            },
                    },
}


# Folders used by the controller code
BASE_FRONTEND_DATA_DIR = os.path.join( BASE_DATA_DIR, 'frontend_data')
PATHS = {
    'classifiers' : os.path.join( BASE_FRONTEND_DATA_DIR, 'searchdata', 'classifiers'),
    'postrainimgs' : os.path.join( BASE_FRONTEND_DATA_DIR, 'searchdata', 'postrainimgs'),
    'uploadedimgs' : os.path.join( BASE_FRONTEND_DATA_DIR, 'searchdata', 'uploadedimgs'),
    'rankinglists' : os.path.join( BASE_FRONTEND_DATA_DIR, 'searchdata', 'rankinglists'),
    'predefined_rankinglists' : os.path.join( BASE_FRONTEND_DATA_DIR, 'searchdata', 'predefined_rankinglists'),
    'postrainanno' : os.path.join( BASE_FRONTEND_DATA_DIR, 'searchdata', 'postrainanno'),
    'postrainfeats' : os.path.join( BASE_FRONTEND_DATA_DIR, 'searchdata', 'postrainfeats'),
    'curatedtrainimgs' : os.path.join( BASE_FRONTEND_DATA_DIR, 'curatedtrainimgs'),
    'datasets' : os.path.join( BASE_DATA_DIR, 'datasets', 'images'),
    'thumbnails' : os.path.join( BASE_DATA_DIR, 'datasets', 'images'), # keep this one the same as 'datasets' unless thumbnails are really provided
    'regions' : os.path.join( BASE_DATA_DIR, 'datasets', 'images'), # The ROIs are defined over the original images
}

# Folders containing metadata
METADATA = {
    'metadata' : os.path.join( BASE_DATA_DIR, 'datasets', 'metadata')
}

# Settings of the visor engine
RETENGINE = {
    'pool_workers' : 8,
    'resize_width' : 560,
    'resize_height' : 420,
    'disable_cache' : False,
    'rf_rank_type' : 'full',
    'rf_rank_topn' : 2000,
    'rf_train_type' : 'regular',
    'feat_detector_type': 'fast'
}

# Settings for image search tool
IMSEARCHTOOLS = {
    'service_host' : 'localhost',
    'service_port' : 36213,
    'engine' : 'google_web',
    'query_timeout' : -1.0,
    'improc_timeout' : 8,
    'per_image_timeout' : 3.0,
    'num_pos_train' : 100,
}

# Base folder of scripts to manage the service
MANAGE_SERVICE_SCRIPTS_BASE_PATH = os.path.join(BASE_DIR, 'scripts')


######
# General Data Ingestion settings
######

# Size of the chunks in which list of frames will be divided.
PREPROC_CHUNK_SIZE = 500

# Limit to the number of threads to be started when ingesting new data.
# Each thread will be assigned one chunk of data.
FRAMES_THREAD_NUM_LIMIT = 6

# Maximum number of individual files to be uploaded
MAX_NUMBER_UPLOAD_INDIVIDUAL_FILES = 500

# Maximum amount of bytes when uploading individual files
MAX_TOTAL_SIZE_UPLOAD_INDIVIDUAL_FILES = MAX_NUMBER_UPLOAD_INDIVIDUAL_FILES * 1024 * 1024

# Minimum number of ingested individual files begore starting pipeline_input thread
MIN_NUMBER_INPUT_THREAD_INDIVIDUAL_FILES = 1000000

# Set a minimum set of valid image extensions. This is to check whether a file is an image or not
# WITHOUT actually reading the file, because checking all files is too expensive when large amounts
# of images are ingested.
VALID_IMG_EXTENSIONS = { ".jpeg", ".jpg", ".png", ".bmp", ".dib", ".tiff", ".tif", ".ppm" }
VALID_IMG_EXTENSIONS_STR = ', '.join(VALID_IMG_EXTENSIONS) # '.txt' is added later in the admin view

######
# Face search engine - Data Ingestion settings
######

# Setup settings for face-search engine
FACE_ENGINE_SETTINGS = {}
FACE_ENGINE_SETTINGS['FACES_DATASET_IM_BASE_PATH'] = os.path.join( PATHS['datasets'], VISOR['datasets'].keys()[0] )
FACE_ENGINE_SETTINGS['FACES_DATASET_IM_PATHS'] = os.path.join( BASE_DATA_DIR, 'backend_data', 'faces', 'dsetpaths.txt')
FACE_ENGINE_SETTINGS['FACES_NEGATIVE_IM_PATHS'] = None
FACE_ENGINE_SETTINGS['FACES_NEGATIVE_IM_BASE_PATH'] = None
FACE_ENGINE_SETTINGS['FACES_DATASET_FEATS_FILE'] = os.path.join( BASE_DATA_DIR, 'backend_data', 'faces', 'features', 'database.pkl')
FACE_ENGINE_SETTINGS['FACES_NEG_FEATS_FILE'] = None
