#!/usr/bin/bash
#exit on error
set -o errexit

#install dependencies (optional if using the default build command , but useful for clarity)
python3 -m pip install -r requirements.txt

#collect static files
python3 manage.py collectstatic --no-input

#apply database migrations
python3 manage.py makemigrations
python3 manage.py migrate
