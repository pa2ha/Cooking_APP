all: run

run:
    gunicorn --bind 0.0.0.0:8000 foodgram.wsgi
