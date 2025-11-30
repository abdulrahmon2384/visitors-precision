#!/bin/sh
source .venv/bin/activate
gunicorn main:app --bind 0.0.0.0:$PORT
