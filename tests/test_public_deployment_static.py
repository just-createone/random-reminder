from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_public_compose_keeps_application_port_private() -> None:
    content = (
        PROJECT_ROOT / "compose.public.yaml"
    ).read_text(encoding="utf-8")

    app_section = content.split("  caddy:\n", maxsplit=1)[0]

    assert "random-reminder-public-app" in app_section
    assert "    ports:\n" not in app_section
    assert 'RANDOM_REMINDER_SESSION_COOKIE_SECURE: "true"' in app_section


def test_public_compose_exposes_only_caddy_web_ports() -> None:
    content = (
        PROJECT_ROOT / "compose.public.yaml"
    ).read_text(encoding="utf-8")

    caddy_section = content.split("  caddy:\n", maxsplit=1)[1]

    assert "caddy:2.11.4-alpine" in caddy_section
    assert '- "80:80"' in caddy_section
    assert '- "443:443"' in caddy_section
    assert '- "443:443/udp"' in caddy_section
    assert "APP_DOMAIN" in caddy_section
    assert "CADDY_EMAIL" in caddy_section
    assert "./caddy/data:/data" in caddy_section
    assert "./caddy/config:/config" in caddy_section


def test_caddyfile_proxies_to_application_with_basic_headers() -> None:
    content = (
        PROJECT_ROOT / "caddy" / "Caddyfile"
    ).read_text(encoding="utf-8")

    assert "{$APP_DOMAIN}" in content
    assert "reverse_proxy app:8000" in content
    assert "health_uri /health" in content
    assert 'X-Content-Type-Options "nosniff"' in content
    assert 'X-Frame-Options "DENY"' in content
