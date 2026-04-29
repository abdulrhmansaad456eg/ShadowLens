"""
Cryptography Layer for ShadowLens
Provides AES-256-GCM encryption with PBKDF2 key derivation
"""

import os
import base64
import secrets
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from typing import Tuple, Optional


class CryptoManager:
    """
    Manages all cryptographic operations for ShadowLens.
    Uses AES-256-GCM for authenticated encryption.
    """
    
    # PBKDF2 parameters
    ITERATIONS = 600000  # OWASP recommended minimum
    SALT_LENGTH = 32     # 256 bits
    IV_LENGTH = 12       # 96 bits for GCM
    KEY_LENGTH = 32      # 256 bits for AES-256
    
    def __init__(self):
        """Initialize the crypto manager with default backend."""
        self.backend = default_backend()
    
    def generate_salt(self) -> bytes:
        """Generate a cryptographically secure random salt."""
        return secrets.token_bytes(self.SALT_LENGTH)
    
    def generate_iv(self) -> bytes:
        """Generate a cryptographically secure random IV."""
        return secrets.token_bytes(self.IV_LENGTH)
    
    def derive_key(self, password: str, salt: bytes) -> bytes:
        """
        Derive encryption key from password using PBKDF2-HMAC-SHA256.
        
        Args:
            password: User-provided password string
            salt: Random salt bytes
            
        Returns:
            32-byte derived key for AES-256
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.KEY_LENGTH,
            salt=salt,
            iterations=self.ITERATIONS,
            backend=self.backend
        )
        return kdf.derive(password.encode('utf-8'))
    
    def encrypt(self, plaintext: bytes, password: str) -> bytes:
        """
        Encrypt data using AES-256-GCM.
        
        Format of output: salt (32) + iv (12) + ciphertext + auth_tag (16)
        
        Args:
            plaintext: Data to encrypt
            password: Encryption password
            
        Returns:
            Encrypted data with embedded salt and IV
        """
        # Generate random salt and IV
        salt = self.generate_salt()
        iv = self.generate_iv()
        
        # Derive key from password
        key = self.derive_key(password, salt)
        
        # Create AES-GCM cipher
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(iv),
            backend=self.backend
        )
        encryptor = cipher.encryptor()
        
        # Encrypt plaintext
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        
        # Get authentication tag
        auth_tag = encryptor.tag
        
        # Combine: salt + iv + ciphertext + auth_tag
        encrypted_data = salt + iv + ciphertext + auth_tag
        
        return encrypted_data
    
    def decrypt(self, encrypted_data: bytes, password: str) -> Optional[bytes]:
        """
        Decrypt data using AES-256-GCM.
        
        Args:
            encrypted_data: Data in format: salt (32) + iv (12) + ciphertext + auth_tag (16)
            password: Decryption password
            
        Returns:
            Decrypted plaintext or None if decryption fails
        """
        try:
            # Extract components
            salt = encrypted_data[:self.SALT_LENGTH]
            iv = encrypted_data[self.SALT_LENGTH:self.SALT_LENGTH + self.IV_LENGTH]
            auth_tag = encrypted_data[-16:]  # Last 16 bytes
            ciphertext = encrypted_data[self.SALT_LENGTH + self.IV_LENGTH:-16]
            
            # Derive key from password
            key = self.derive_key(password, salt)
            
            # Create AES-GCM cipher
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(iv, auth_tag),
                backend=self.backend
            )
            decryptor = cipher.decryptor()
            
            # Decrypt ciphertext
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            return plaintext
            
        except Exception:
            # Authentication failed or other error
            return None
    
    def encrypt_to_base64(self, plaintext: bytes, password: str) -> str:
        """
        Encrypt and encode to base64 for text transport.
        
        Args:
            plaintext: Data to encrypt
            password: Encryption password
            
        Returns:
            Base64-encoded encrypted data
        """
        encrypted = self.encrypt(plaintext, password)
        return base64.b64encode(encrypted).decode('utf-8')
    
    def decrypt_from_base64(self, b64_ciphertext: str, password: str) -> Optional[bytes]:
        """
        Decode from base64 and decrypt.
        
        Args:
            b64_ciphertext: Base64-encoded encrypted data
            password: Decryption password
            
        Returns:
            Decrypted plaintext or None if decryption fails
        """
        try:
            encrypted = base64.b64decode(b64_ciphertext)
            return self.decrypt(encrypted, password)
        except Exception:
            return None
    
    def get_encryption_overhead(self) -> int:
        """
        Get the overhead size added by encryption (salt + iv + auth_tag).
        
        Returns:
            Number of overhead bytes
        """
        return self.SALT_LENGTH + self.IV_LENGTH + 16  # 16 bytes for GCM tag
