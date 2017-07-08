FROM python:2.7

MAINTAINER Johann Schmitz

RUN apt-get update -y && apt-get upgrade -y && \
	apt-get install nginx supervisor rrdtool -y

RUN mkdir -p /code
WORKDIR /code

EXPOSE 8080

ADD . /code/app
WORKDIR /code/app
RUN chown nobody:nogroup /code -R && python -m compileall /code/app

# installing gunicorn via pip3 installs the python3 version
RUN pip install -r requirements.txt && \
	pip install mysqlclient gunicorn

COPY docker/nginx.conf /etc/nginx/conf.d/
COPY docker/supervisord.conf /etc/supervisord.conf

ENV DJANGO_SETTINGS_MODULE docker_settings

CMD /usr/bin/supervisord -c /etc/supervisord.conf -n
