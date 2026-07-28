import base64
from pathlib import Path

from cryptography.hazmat.primitives import (
    serialization,
)
from cryptography.hazmat.primitives.asymmetric import (
    ec,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

VAPID_DIRECTORY = (
    PROJECT_ROOT
    / "secrets"
    / "vapid"
)

PRIVATE_KEY_PATH = (
    VAPID_DIRECTORY
    / "private_key.pem"
)

PUBLIC_KEY_PATH = (
    VAPID_DIRECTORY
    / "public_key.pem"
)

APPLICATION_SERVER_KEY_PATH = (
    VAPID_DIRECTORY
    / "application_server_key.txt"
)


def main() -> None:
    """生成 Web Push 使用的 VAPID 密钥。"""

    VAPID_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    existing_files = [
        path
        for path in (
            PRIVATE_KEY_PATH,
            PUBLIC_KEY_PATH,
            APPLICATION_SERVER_KEY_PATH,
        )
        if path.exists()
    ]

    if existing_files:
        raise RuntimeError(
            "VAPID 密钥已经存在，"
            "为避免已有订阅失效，本次未覆盖。"
        )

    private_key = ec.generate_private_key(
        ec.SECP256R1()
    )

    public_key = private_key.public_key()

    private_key_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=(
            serialization.NoEncryption()
        ),
    )

    public_key_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=(
            serialization.PublicFormat
            .SubjectPublicKeyInfo
        ),
    )

    application_server_key_bytes = (
        public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=(
                serialization.PublicFormat
                .UncompressedPoint
            ),
        )
    )

    application_server_key = (
        base64.urlsafe_b64encode(
            application_server_key_bytes
        )
        .decode("ascii")
        .rstrip("=")
    )

    PRIVATE_KEY_PATH.write_bytes(
        private_key_bytes
    )

    PUBLIC_KEY_PATH.write_bytes(
        public_key_bytes
    )

    APPLICATION_SERVER_KEY_PATH.write_text(
        application_server_key,
        encoding="utf-8",
    )

    print("VAPID 密钥生成成功：")
    print(PRIVATE_KEY_PATH)
    print(PUBLIC_KEY_PATH)
    print(APPLICATION_SERVER_KEY_PATH)


if __name__ == "__main__":
    main()