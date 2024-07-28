from pathlib import Path

import typed_settings as ts


@ts.settings
class TelegramInbox:
    chat_id: str
    emails: list[str]


@ts.settings
class TelegramSettings:
    token: str
    catch_all_chat_id: int
    inboxes: list[TelegramInbox] = []

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
class SpamSettings:
    dnsbl: str | None = None
    blacklist: list[str] = []


@ts.settings
class Settings:
    hostname: str
    telegram: TelegramSettings
    smtp: SMTPSettings

    eml_path: Path
    spam: SpamSettings


config: Settings = ts.load(Settings, appname="smtg", config_files=["config.toml"])


__all__ = ["config"]
