bind = '192.168.139.2:4004'
wsgi_app = 'rivercureproject.wsgi'
# Workers silent for more than this many seconds are killed and restarted.
timeout = '1800'
workers = 4
accesslog = '~/logs/rivercure/access.log'
acceslogformat = "%(h)s %(l)s %(u)s %(t)s %(r)s %(s)s %(b)s %(f)s %(a)s"
errorlog = '~/logs/rivercure/error.log'
