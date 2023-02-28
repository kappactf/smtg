import html
import io
from asyncio import AbstractEventLoop
from dataclasses import dataclass, field
from email.message import EmailMessage
from typing import Any

import aiogram
from aiogram.types import InputFile, InputMedia, InputMediaDocument, MediaGroup

from smtg.config import config
from smtg.parsers import HTMLSimplifier, HTMLSplitter


@dataclass
class ConvertedMessage:
    html_parts: list[str] = field(default_factory=list)
    attachments: list[InputFile] = field(default_factory=list)


def create_bot(loop: AbstractEventLoop) -> aiogram.Bot:
    return aiogram.Bot(
        token=config.telegram.token,
        parse_mode="HTML",
        disable_web_page_preview=True,
        loop=loop
    )


def wrap_io(message) -> io.IOBase:
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
    def __init__(self, bot: aiogram.Bot):
        self.bot = bot

    async def __call__(self, _recipients: list[str], message: EmailMessage) -> list[str]:
        prepared_message = convert_message(message)

        message_id = None

        for part in prepared_message.html_parts:
            telegram_message = await self.bot.send_message(
                config.telegram.chat_id,
                part,
                reply_to_message_id=message_id
            )
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
                await self.bot.send_media_group(
                    config.telegram.chat_id,
                    MediaGroup(medias),  # type: ignore (wtf?)
                    reply_to_message_id=message_id
                )

        return []
