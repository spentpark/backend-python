"""Configuración común de las pruebas.

Fija el entorno JWT **antes** de importar la aplicación y eleva los límites de
rate limiting para que la suite no se auto-bloquee (mismo enfoque que
``__test__/setup-env.js`` del backend Node).
"""
import os

import bcrypt

TEST_JWT_SECRET = "test-secret-0123456789abcdef0123456789abcdef"
TEST_USERNAME = "admin"
TEST_PASSWORD = "test-password"
TEST_ROLE = "admin"

os.environ["ENVIRONMENT"] = "test"
os.environ["JWT_SECRET"] = TEST_JWT_SECRET
os.environ["JWT_EXPIRES_IN"] = "1h"
os.environ["JWT_ISSUER"] = "rss-game-node"
os.environ["JWT_AUDIENCE"] = "rss-game-node-api"
os.environ["AUTH_USERNAME"] = TEST_USERNAME
os.environ["AUTH_ROLE"] = TEST_ROLE
os.environ["AUTH_PASSWORD_HASH"] = bcrypt.hashpw(
    TEST_PASSWORD.encode("utf-8"), bcrypt.gensalt(rounds=4)
).decode("utf-8")
os.environ["API_RATE_LIMIT_MAX"] = "100000"
os.environ["AUTH_RATE_LIMIT_MAX"] = "100000"
os.environ["API_DOCS_ENABLED"] = "true"
