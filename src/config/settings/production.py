# ruff: noqa: F401
"""Django `production` settings for config project.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

import os

import dj_database_url
from dj_database_url import DEFAULT_ENV
from django.core.exceptions import ImproperlyConfigured

from config.settings.common.base import *
from config.settings.common.database import DATABASES
from config.settings.common.security import (
    CSRF_COOKIE_SECURE,
    SECURE_CONTENT_TYPE_NOSNIFF,
    SECURE_HSTS_INCLUDE_SUBDOMAINS,
    SECURE_HSTS_PRELOAD,
    SECURE_HSTS_SECONDS,
    SECURE_PROXY_SSL_HEADER,
    SECURE_REFERRER_POLICY,
    SESSION_COOKIE_SECURE,
    USE_X_FORWARDED_HOST,
    X_FRAME_OPTIONS,
)
from config.settings.environment.django import (
    ALLOWED_HOSTS,
    DEBUG,
    ENVIRONMENT,
    SECRET_KEY,
)
from config.settings.environment.service import (
    AFRICAS_TALKING_API_KEY,
    AFRICAS_TALKING_USERNAME,
    OIDC_RP_CLIENT_ID,
    OIDC_RP_CLIENT_SECRET,
)

if DEFAULT_ENV not in os.environ:
    errmsg = "Required DATABASE_URL environment variable not set"
    raise ImproperlyConfigured(errmsg)

RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Override to use DB URL expected in target PaaS.
DATABASES["default"] = dj_database_url.config(
    conn_max_age=500,
    conn_health_checks=True,
)

# Silenced checks not output to the console.
# See: https://docs.djangoproject.com/en/4.2/ref/checks/
SILENCED_SYSTEM_CHECKS = [
    # W008 = `SECURE_SSL_REDIRECT = False`
    #
    # Reason:
    #   Site runs behind a TLS-terminating reverse proxy that redirects all HTTP
    #   requests to HTTPS. Given proxy forwarded requests to the site will be
    #   insecure (non-HTTPS), this may cause infinite redirects.
    "security.W008",
]
