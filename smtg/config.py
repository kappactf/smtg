from pathlib import Path

import typed_settings as ts


@ts.settings
class TelegramSettings:
    token: str
    chat_id: int

@ts.settings
class TLSSettings:
    key_path: str
    cert_path: str
    key_passphrase: str | None = None


@ts.settings
class SMTPSettings:
    host: str = "*"
    port: int = 25
    tls: TLSSettings | None = None


@ts.settings
class Settings:
    hostname: str
    telegram: TelegramSettings
    smtp: SMTPSettings

    eml_path: Path
    dnsbl: str | None = None


config: Settings = ts.load(Settings, appname="smtg", config_files=["config.toml"])  # type: ignore (WTF?)


__all__ = ["config"]
