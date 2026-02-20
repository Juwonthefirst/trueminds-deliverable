import hashlib
import secrets

from fastapi import HTTPException


class OTPVerificationError(HTTPException):
    def __init__(self):
        super().__init__(status_code=401, detail="Invalid OTP")


class OTPValidationAttemptsExceededError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=429, detail="Too many failed attempts, Request for a new token"
        )


class OTPServices:
    OTP_EXPIRY_TIME = 600
    MAX_ATTEMPTS = 5

    @classmethod
    def generate_otp(cls) -> list[str]:
        otp = "".join([str(secrets.randbelow(10)) for _ in range(6)])
        otp_hash = hashlib.sha256(otp.encode()).hexdigest()
        print(otp)
        return [otp, otp_hash]

    @classmethod
    def verify_otp(cls, otp: str, stored_otp_hash: str) -> bool:
        otp_hash = hashlib.sha256(otp.encode()).hexdigest()
        return secrets.compare_digest(otp_hash, stored_otp_hash)
