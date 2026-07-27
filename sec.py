from os import getenv

import jwt

secret_key = getenv("secret_key")
algorithm = getenv("algorithm", "")


def create_tk(data: dict):
    return jwt.encode(payload=data, key=secret_key, algorithm=algorithm)


def read_tk(tk):
    try:
        return jwt.decode(jwt=tk, key=secret_key, algorithms=[algorithm])
    except jwt.InvalidTokenError:
        return None
