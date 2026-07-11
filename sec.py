import jwt, env

def create_tk(data: dict):
    return jwt.encode(payload=data, key=env.SECRET_KEY,
                      algorithm=env.ALGORITHM)

def read_tk(tk):
    try:
        return jwt.decode(jwt=tk, key=env.SECRET_KEY,
                          algorithms=[env.ALGORITHM])
    except jwt.InvalidTokenError:
        return None