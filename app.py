#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import os
import ssl

import sys
from aiosmtpd.controller import Controller
from aiosmtpd.smtp import SMTP

from inbox import MailHandler
from bot import send_message
from config import *

handler = MailHandler()

@handler.default_route
def process(message, dkim, spf):
    send_message(message, dkim, spf)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    ssl_context = None

    if os.path.exists("keys/host.crt") and os.path.exists("keys/host.key"):
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain("keys/host.crt", "keys/host.key")

    controller = Controller(handler, hostname=SMTP_HOST, port=SMTP_PORT)

    controller.factory = lambda: SMTP(handler, enable_SMTPUTF8=True, tls_context=ssl_context)
    controller.start()

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        controller.stop()
        loop.stop()
        loop.close()

