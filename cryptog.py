import base64
import os
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet

def derive_key(password: str, salt: bytes = None) -> bytes:
    if not salt:
        salt = os.urandom(16)  # Generate a random salt if none provided
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key, salt

def encrypt_message(message: str, password: str) -> (str, bytes):
    key, salt = derive_key(password)
    f = Fernet(key)
    encrypted_message = f.encrypt(message.encode())
    return encrypted_message.decode(), salt

def decrypt_message(encrypted_message: str, password: str, salt: bytes) -> str:
    key, _ = derive_key(password, salt)
    f = Fernet(key)
    return f.decrypt(encrypted_message.encode()).decode()

def get_private_key() -> str:
    try:
        with open('private_key.txt', 'r') as file:
            encrypted_message = file.read().strip()
    except FileNotFoundError:
        raise Exception("The private_key.txt file was not found.")
    except IOError:
        raise Exception("An error occurred while reading the private_key.txt file.")
    
    salt = b' !\xdc\xc3\xc3wS\xe2\xe9\xa3>d\xa3\xaa\x9e\x99'
    password = os.getenv('cryptog_password')
    
    if not password:
        raise Exception("The environment variable 'cryptog_password' is not set.")
    
    try:
        decrypted_message = decrypt_message(encrypted_message, password, salt)
    except Exception as e:
        raise Exception(f"An error occurred during decryption: {e}")
    
    return decrypted_message

get_private_key()