from datetime import datetime, timedelta, timezone
import hashlib
import re
import secrets
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pwdlib import PasswordHash

from backend.domain.user import User
from backend.repository.session_repository import SessionRepository
from backend.repository.user_repository import UserRepository


class AuthenticationError(Exception):
    """Credentials or session are not valid."""


class EmailAlreadyRegisteredError(Exception):
    """A registration email already exists."""


class AuthService:
    """Register users and manage opaque browser sessions."""

    _EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

    def __init__(
        self,
        user_repository: UserRepository | None = None,
        session_repository: SessionRepository | None = None,
        password_hash: PasswordHash | None = None,
    ) -> None:
        self.user_repository = user_repository or UserRepository()
        self.session_repository = session_repository or SessionRepository()
        self.password_hash = password_hash or PasswordHash.recommended()
        self._dummy_password_hash = self.password_hash.hash(
            "not-a-real-user-password"
        )

    def register(
        self,
        email: str,
        password: str,
        time_zone: str = "Asia/Shanghai",
    ) -> User:
        normalized_email = self._validate_email(email)
        self._validate_password(password)
        validated_time_zone = self._validate_time_zone(time_zone)

        if (
            self.user_repository.get_by_email_with_password_hash(
                normalized_email
            )
            is not None
        ):
            raise EmailAlreadyRegisteredError()

        try:
            user = self.user_repository.create(
                normalized_email,
                self.password_hash.hash(password),
                validated_time_zone,
            )
            self.user_repository.provision_user_data(user.id)
            return user
        except Exception as error:
            if "UNIQUE constraint failed: users.email" in str(error):
                raise EmailAlreadyRegisteredError() from error
            raise

    def login(self, email: str, password: str) -> User:
        normalized_email = self._normalize_email(email)
        result = self.user_repository.get_by_email_with_password_hash(
            normalized_email
        )

        if result is None:
            self.password_hash.verify(
                password,
                self._dummy_password_hash,
            )
            raise AuthenticationError()

        user, password_hash = result

        if not self.password_hash.verify(password, password_hash):
            raise AuthenticationError()

        return user

    def create_session(self, user_id: int, duration_days: int) -> str:
        session_token = secrets.token_urlsafe(32)
        session_token_hash = self._hash_session_token(session_token)
        expires_at = datetime.now(timezone.utc) + timedelta(days=duration_days)

        self.session_repository.create(
            session_token_hash,
            user_id,
            expires_at,
        )

        return session_token

    def get_user_for_session_token(self, session_token: str | None) -> User:
        if not session_token:
            raise AuthenticationError()

        user = self.session_repository.get_user_by_token_hash(
            self._hash_session_token(session_token)
        )

        if user is None:
            raise AuthenticationError()

        return user

    def revoke_session(self, session_token: str | None) -> None:
        if session_token:
            self.session_repository.delete_by_token_hash(
                self._hash_session_token(session_token)
            )

    @classmethod
    def _normalize_email(cls, email: str) -> str:
        return email.strip().lower()

    @classmethod
    def _validate_email(cls, email: str) -> str:
        normalized_email = cls._normalize_email(email)

        if len(normalized_email) > 254 or not cls._EMAIL_PATTERN.fullmatch(
            normalized_email
        ):
            raise ValueError("请输入有效的邮箱地址")

        return normalized_email

    @staticmethod
    def _validate_password(password: str) -> None:
        if len(password) < 8:
            raise ValueError("密码至少需要 8 个字符")

        if len(password) > 128:
            raise ValueError("密码不能超过 128 个字符")

    @staticmethod
    def _validate_time_zone(time_zone: str) -> str:
        normalized_time_zone = time_zone.strip()

        try:
            ZoneInfo(normalized_time_zone)
        except (ZoneInfoNotFoundError, ValueError) as error:
            raise ValueError("浏览器时区无效") from error

        return normalized_time_zone

    @staticmethod
    def _hash_session_token(session_token: str) -> str:
        return hashlib.sha256(
            session_token.encode("utf-8")
        ).hexdigest()
