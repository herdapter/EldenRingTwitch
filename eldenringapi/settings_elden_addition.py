import os

# Ajout pour sett&ings.py

# Elden Ring Parser Settings
ELDEN_PARSER_URL = os.environ.get('ELDEN_PARSER_URL', 'http://localhost:3002')
ELDEN_PARSER_TIMEOUT = 30

# Cache (si pas déjà configuré)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'services.elden_parser': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}
