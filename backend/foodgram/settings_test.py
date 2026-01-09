from .settings import *  # noqa
from .settings import BASE_DIR

SECRET_KEY = 'test-secret-key-for-ci-only'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'test_db.sqlite3',
    }
}

print('Using test settings with SQLite database.')
