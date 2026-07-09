import os


SECRET_KEY = os.environ.get(
    "SUPERSET_SECRET_KEY",
    "local-dev-smart-meter-secret-change-me",
)

SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(
    os.environ.get("SUPERSET_HOME", os.path.abspath("superset_home")),
    "superset.db",
)

FEATURE_FLAGS = {
    "ENABLE_TEMPLATE_PROCESSING": True,
}

TALISMAN_ENABLED = False
WTF_CSRF_ENABLED = True
