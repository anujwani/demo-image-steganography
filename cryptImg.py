import secrets
from base64 import urlsafe_b64decode as b64d, urlsafe_b64encode as b64e

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

import io

class cryptImg:

    def __init__(self, iterations=100_000) -> None:    
        self.backend = default_backend()
        self.iterations = iterations


    # generate key
    def _derive_key(self, password: bytes, salt: bytes, iterations: int) -> bytes:
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256, length=32, salt=salt, iterations=iterations, backend=self.backend)
        return b64e(kdf.derive(password))


    # encrypt
    def _password_encrypt(self, message: str, password: str) -> bytes:
        salt = secrets.token_bytes(16)
        key = self._derive_key(password.encode(), salt, self.iterations)
        return b64e(
            b'%b%b%b' % (
                salt,
                self.iterations.to_bytes(4, 'big'),
                b64d(Fernet(key).encrypt(message.encode()))
            )
        )


    # decrypt
    def _password_decrypt(self, token: bytes, password: str) -> str:
        decoded = b64d(token)
        salt, iters, token = decoded[:16], decoded[16:20], b64e(decoded[20:])
        iterations = int.from_bytes(iters, 'big')
        key = self._derive_key(password.encode(), salt, iterations)

        try:
            decrypted_text = Fernet(key).decrypt(token)
            return decrypted_text.decode(), 0
        except InvalidToken:
            # print('Wrong pass')
            return None, -1
        except Exception:
            return None, 1


    # read
    def getMessage(self, fp: io.BufferedReader, content: bytes = None, password: str = None, delete_on_read: bool = True) -> str:
        # no content
        if content is None:
            content = fp.read()

        offset = content.find(bytes.fromhex('FFD9'))
        fp.seek(offset + 2)

        token = fp.read()
        
        message = None
        status = 1
        if token:
            if delete_on_read:
                fp.flush()
                fp.seek(offset + 2)
                fp.truncate()

            message, status = self._password_decrypt(token=token, password=password)
            
        return message, status
        

    # write
    def embedMsg(self, fp: io.BufferedReader, content: bytes = None, message: str = '', password: str = None, clear_history: bool = True) -> bool:
        # no content
        if content is None:
            content = fp.read()

        offset = content.find(bytes.fromhex('FFD9'))
        fp.seek(offset + 2)

        if fp.read() and clear_history:
            fp.flush()
            fp.seek(offset + 2)
            fp.truncate()

        encrypted_message = self._password_encrypt(message, password)
        fp.write(encrypted_message)

        return True


    # delete
    def delMsg(self, fp: io.BufferedReader, content: bytes = None) -> None:
        # no content
        if content is None:
            content = fp.read()

        offset = content.find(bytes.fromhex('FFD9'))

        fp.flush()
        fp.seek(offset+2)
        fp.truncate()
