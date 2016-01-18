#!/usr/bin/env bash
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

PYTHONPATH="${PYTHONPATH}:${DIR}:." DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:=dev_settings}" python manage.py $*
