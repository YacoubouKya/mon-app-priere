"""Genere le hash bcrypt d'un mot de passe et une cle de cookie aleatoire.

Usage : python scripts/hash_password.py
"""

import getpass
import secrets

import bcrypt


def main() -> None:
    password = getpass.getpass("Mot de passe a hasher : ")
    if not password:
        raise SystemExit("Mot de passe vide.")
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()
    print(f"\nHash bcrypt     : {hashed}")
    print(f"Cle de cookie   : {secrets.token_urlsafe(32)}")


if __name__ == "__main__":
    main()
