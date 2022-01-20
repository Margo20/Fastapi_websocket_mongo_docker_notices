import os
import sys
import base64
import hashlib


def fastapi_crypt_pass(password: str, salt_bytes: bytes) -> bytes:
    password_bytes = password.encode()
    hash_bytes = hashlib.scrypt(password=password_bytes, salt=salt_bytes, n=16384, r=8, p=1)
    return hash_bytes


if __name__ == '__main__':
    password = sys.argv[1]
    print('FASTAPI_PASSWORD = \'' + password + '\'')

    salt_bytes = os.urandom(16)
    salt_base64 = base64.b64encode(salt_bytes).decode()
    print('SALT_BASE64 = \'' + salt_base64 + '\'')

    hash_bytes = fastapi_crypt_pass(password, salt_bytes)
    hash_base64 = base64.b64encode(hash_bytes).decode()
    print('HASH_BASE64 = \'' + hash_base64 + '\'')
