# -*- coding: utf-8 -*-

from djunin.settings import *

import os
import logging

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

DEBUG = False
ALLOWED_HOSTS = [x.strip() for x in os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',')]

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s %(levelname)-7s %(message)s'
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DJANGO_DATABASE_NAME'),
        'USER': os.environ.get('DJANGO_DATABASE_USER'),
        'PASSWORD': os.environ.get('DJANGO_DATABASE_PASS'),
        'HOST': os.environ.get('DJANGO_DATABASE_HOST'),
        'PORT': os.environ.get('DJANGO_DATABASE_PORT', ''),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        }
    }
}

MUNIN_DATA_DIR = '/munin'

COMPRESS_ROOT = os.path.join(BASE_DIR, 'djunin/static')
