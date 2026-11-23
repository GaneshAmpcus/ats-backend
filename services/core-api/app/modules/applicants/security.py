"""Encryption helpers for sensitive applicant identity numbers.

Covers ``applicants.pan_number``, ``applicants.aadhaar_number`` and
``applicants.passport_number`` (DPDP-Act sensitive data).

IMPLEMENTATION REQUIRED
-----------------------
The encryption mechanism (application-level cipher, pgcrypto, KMS, key
management and rotation) has not been decided. The helpers below are
intentionally unimplemented and raise ``NotImplementedError``. This is
fail-closed: no identity number can be written to the database in plaintext
until a real implementation is provided.

Once implemented, only ``encrypt_identity_value`` and ``decrypt_identity_value``
need to change; the ORM column type below and the models do not.
"""

from typing import Any

from sqlalchemy import LargeBinary
from sqlalchemy.types import TypeDecorator


def encrypt_identity_value(plaintext: str) -> bytes:
    """Encrypt a plaintext identity number (PAN, Aadhaar or passport).

    Args:
        plaintext: The raw identity number.

    Returns:
        The encrypted value as bytes, suitable for storage in a binary column.

    Raises:
        NotImplementedError: Always, until an encryption implementation is added.
    """
    raise NotImplementedError(
        "Identity number encryption is not implemented. "
        "Implement encrypt_identity_value in app/modules/applicants/security.py."
    )


def decrypt_identity_value(ciphertext: bytes) -> str:
    """Decrypt a stored identity number back to plaintext.

    Args:
        ciphertext: The encrypted bytes read from the database.

    Returns:
        The plaintext identity number.

    Raises:
        NotImplementedError: Always, until an encryption implementation is added.
    """
    raise NotImplementedError(
        "Identity number decryption is not implemented. "
        "Implement decrypt_identity_value in app/modules/applicants/security.py."
    )


class EncryptedIdentityNumber(TypeDecorator):
    """Binary column type that transparently encrypts and decrypts on the way in/out.

    ``NULL`` passes through untouched. Any non-null value is routed through
    ``encrypt_identity_value`` / ``decrypt_identity_value``.
    """

    impl = LargeBinary
    cache_ok = True

    def process_bind_param(self, value: str | None, dialect: Any) -> bytes | None:
        if value is None:
            return None
        return encrypt_identity_value(value)

    def process_result_value(self, value: bytes | None, dialect: Any) -> str | None:
        if value is None:
            return None
        return decrypt_identity_value(value)
