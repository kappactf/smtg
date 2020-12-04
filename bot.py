#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from config import *
from telegram import *
import re
from email.header import decode_header
from parser import TelegramHTMLParser
import quopri
import hashlib
import io
import time
import os
import traceback

bot = Bot(TOKEN)

def sanitize_fn(text):
    try:
        value = quopri.decodestring(text)
    except e:
        traceback.print_exc(e)
        value = text

    if "." in text:
        ext = text.split(".")[-1]
    else:
        ext = "q"

    if text.isalnum() and len(text) < 42:
        return text
    elif text[:30].isalnum():
        return text[:30] + "." + ext
    else:
        return hashlib.md5(text.encode()).hexdigest() + "." + ext


def decode(text):
    return ''.join(
        t[0].decode() if isinstance(t[0], bytes) else t[0]
        for t in decode_header(text))

def safe(text):
    return decode(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def message_content(message):
    if message.is_multipart():
        return '\n\n'.join(list(map(message_content, message.get_payload())))
    elif message.get_content_type() == "text/html" or message.get_content_type() == "text/plain":
        parser = TelegramHTMLParser()
        message = message.get_payload(decode=True).decode('utf-8')
        message = re.sub(r"(\r\n|\r)", "\n", message)
        message = re.sub(r"\s+", " ", message)
        message = re.sub(r"(\n\s)+\n", "\n", message)
        message = re.sub(r"\n", "", message)
        parser.feed(message)
        return parser.output
        # return safe(message.get_payload(decode=True).decode('utf-8'))
    else:
        fn = f"{int(time.time())}-{sanitize_fn(message.get_filename(failobj='file'))}"
        with open(os.path.join(MEDIA_PATH, fn), "wb") as f:
            f.write(message.get_payload(decode=True))
        return f"Attachment {message.get_content_type()}, {len(message.get_payload())} bytes, {MEDIA_ROOT_URL}/{fn}"

def send_message(message, dkim=False, spf=False):
    print(message.items())
    text=f'''\ud83d\udce7 <b>{safe(message.get("Subject", ""))}</b>
{safe(message.get("from", ""))} → {safe(message.get("To", ""))}

{message_content(message)}
'''
    if not dkim:
        text += "\n\u26a0\ufe0f <i>DKIM is not verified</i>"
    if not spf:
        text += "\n\u26a0\ufe0f <i>SPF is not verified</i>"
    if len(text)<4096:
        try:
            bot.send_message(
                chat_id=CHAT_ID,
                text=text,
                parse_mode="HTML"
            )
        except:
            bot.send_message(
                chat_id=CHAT_ID,
                text=text
            )
    else:
        for x in range(0, len(text), 4096):
            try:
                bot.send_message(
                    chat_id=CHAT_ID,
                    text=text[x:x+4096],
                    parse_mode="HTML"
                )
                time.sleep(0.3)
            except:
                bot.send_message(
                    chat_id=CHAT_ID,
                    text=text[x:x+4096]
                )
