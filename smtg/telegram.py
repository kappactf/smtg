import html
import io
from asyncio import AbstractEventLoop
from dataclasses import dataclass, field
from email.message import EmailMessage, MIMEPart

import aiogram
from aiogram.client.default import DefaultBotProperties
from aiogram.types import InputFile, InputMedia, InputMediaDocument

from smtg.config import config
from smtg.parsers import HTMLSimplifier, HTMLSplitter


@dataclass
class ConvertedMessage:
    html_parts: list[str] = field(default_factory=list)
    attachments: list[InputFile] = field(default_factory=list)


def create_bot() -> aiogram.Bot:
    return aiogram.Bot(
        token=config.telegram.token,
        default=DefaultBotProperties(
            parse_mode="HTML",
            link_preview_is_disabled=True
        )
    )


def wrap_io(message: MIMEPart) -> io.IOBase:
    content = message.get_content()
    if isinstance(content, str):
        return io.StringIO(content)
    if isinstance(content, bytes):
        return io.BytesIO(content)
    if isinstance(content, EmailMessage):
        return io.BytesIO(content.as_bytes())
    raise ValueError(f"{type(content)} cannot be converted to IOBase")


def convert_message(message: EmailMessage) -> ConvertedMessage:
    content = f"""📧 <b>{html.escape(message['Subject'], False)}</b>
{html.escape(message['From'], False)} → {html.escape(message['To'], False)}\n\n"""

    body: EmailMessage | None = message.get_body()  # type: ignore
    if body is None:
        content += "<i>Message does not contain body</i>"
    elif body.get_content_type() == "text/html":
        simplifier = HTMLSimplifier()
        simplifier.feed(body.get_content())
        simplifier.close()
        content += simplifier.result.strip()
    elif body.get_content_type() == "text/plain":
        content += html.escape(body.get_content(), False).strip()

    content += "\n"

    if message["X-SPF-Check"] not in ["pass", "neutral"]:
        content += "\n⚠️ <i>Message sender is not verified</i>"
    if message["X-DKIM-Check"] == "fail":
        content += "\n⚠️ <i>Message signature is missing or invalid</i>"

    attachments = [
        InputFile(wrap_io(part), filename=part.get_filename(failobj="Attachment"))
        for part in message.iter_attachments()
    ]

    splitter = HTMLSplitter()
    splitter.feed(content)
    splitter.close()

    return ConvertedMessage(splitter.parts, attachments)


class TelegramRoute:
    def __init__(self, bot: aiogram.Bot, chat_id: int, emails: list[str] | None = None):
        """Add route for sending incoming messages to Telegram.

        Keyword arguments:
        bot -- reference to aiogram bot instance
        chat_id -- Telegram chat ID
        emails -- filter for emails to be processed by this route (default is None, that means catch-all route)
        """
        self.bot = bot
        self.chat_id = chat_id
        self.emails = emails

    def _match_email(route: str, recipient: str) -> bool:
        """Checks if email to [route] should be delivered to [recipient]."""

        route_prefix, _ = route.lower().split("@", 1)
        recipient_prefix, _ = recipient.lower().split("@", 1)

        if route_prefix.contains('+'):
            return recipient_prefix == route_prefix

        recipient_nonplus_prefix, _ = recipient_prefix.split('+', 1)

        return recipient_nonplus_prefix == route_prefix

    async def __call__(self, recipients: list[str], message: EmailMessage) -> list[str]:
        prepared_message = convert_message(message)

        if any(word in prepared_message for word in config.spam.blacklist):
            # It's spam
            return []

        if self.emails is None:
            # Catch-all
            next_recipients = []
        else:
            next_recipients = [
                recipient
                for recipient in recipients
                if all(not self._match_email(route, recipient) for route in self.emails)
            ]

            if next_recipients == recipients:
                # This route does not match.
                return

        message_id = None

        for part in prepared_message.html_parts:
            telegram_message = await self.bot.send_message(self.chat_id, part, reply_to_message_id=message_id)
            if message_id is None:
                message_id = telegram_message.message_id

        match len(prepared_message.attachments):
            case 0:
                ...
            case 1:
                await self.bot.send_document(
                    config.telegram.chat_id,
                    prepared_message.attachments[0],
                    reply_to_message_id=message_id
                )
            case _:
                medias: list[InputMedia] = [
                    InputMediaDocument(media=attachment)
                    for attachment in prepared_message.attachments
                ]
                await self.bot.send_media_group(self.chat_id, medias, reply_to_message_id=message_id)

        return next_recipients
