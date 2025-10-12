from decouple import config


ENV_OPTIONS = [
    "prod",
    "local"
]


ENV_ID = config("DJANGORLAR_ENV_ID", cast=str)