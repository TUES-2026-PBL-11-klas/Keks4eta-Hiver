"""Central password hashing.

New passwords are hashed with Argon2 (the modern default); Bcrypt is kept in the
hasher list so accounts created before the Argon2 switch (their hashes start with
``$2b$``) still verify. pwdlib routes each verify to the matching hasher by prefix.
"""

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher

_hasher = PasswordHash((Argon2Hasher(), BcryptHasher()))


def hash_password(plain: str) -> str:
    return _hasher.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _hasher.verify(plain, hashed)
