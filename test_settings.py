# -*- coding: utf-8 -*-

from djunin.settings import *

import logging

SECRET_KEY = 'TEST-SECRET-KEY'

DEBUG = True

DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.sqlite3',
		'NAME': 'djunin',
	}
}

logging.basicConfig(
	level=logging.ERROR,
	format='%(asctime)s %(levelname)-7s %(message)s',
)

LOGGING = {
	'version': 1,
	'disable_existing_loggers': False,
	'filters': {
		'require_debug_false': {
			'()': 'django.utils.log.RequireDebugFalse'
		}
	},
	'handlers': {
		'mail_admins': {
			'level': 'ERROR',
			'filters': ['require_debug_false'],
			'class': 'django.utils.log.AdminEmailHandler'
		}
	},
	'loggers': {
		'django.request': {
			'handlers': ['mail_admins'],
			'level': 'ERROR',
			'propagate': True,
		},
		'django.db.backends': {
			'propagate': False,
		},
	}
}

MUNIN_DATA_DIR = ''
