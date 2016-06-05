Djunin is a Django-based frontend for [Munin](http://munin-monitoring.org).

Features:

* client-side graph rendering via [d3.js](https://d3js.org/).
* mobile friendly
* searching

# Installation

Install Djunin like any other Django application (see [Deploying Django](https://docs.djangoproject.com/en/dev/howto/deployment/)). Since Djunin accesses Munin's files, the user needs read access to Munin's datadir (typically `/var/lib/munin`).
Djunin uses [django-compressor](https://github.com/django-compressor/django-compressor) so you have to run `manage.py compress` after installation.

The following settings needs to be set in your `settings.py`:

    MUNIN_DATA_DIR - Path to munins data directory

If you are using rrdcached set the following two values too:

    RRDCACHED - path to rrdcached`s socket (e.g. unix:/var/run/rrdcached.sock)
    FLUSH_BEFORE_FETCH=True


# License

See LICENSE.txt
