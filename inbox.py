#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from email import message_from_bytes
from email.message import Message

import dkim
import spf
from aiosmtpd.smtp import Envelope, Session, SMTP

import logging

from config import *


class MailRoute:
    def __init__(self, login, func):
        self._login = login
        self._func = func

    def process(self, address, *args, **kwargs):
        if address.lower() == self._login.lower() + "@" + HOSTNAME.lower():
            self._func(*args, **kwargs)
            return True
        return False


class MailHandler:
    def __init__(self):
        self.handlers = []
        self.default_handler = None

    def route(self, login):
        def decorate(self, func):
            self.handlers.append(MailRoute(login, func))

            return func
        return decorate

    def default_route(self, func):
        if self.default_handler is not None:
            raise ValueError("Only one default route can be set.")
        
        self.default_handler = func

        return func

    async def handle_MAIL(self, server, session, envelope, address, mail_options):
        ip = session.peer[0]
        result, description = spf.check2(ip, address, session.host_name)

        envelope.mail_from = address
        envelope.mail_options.extend(mail_options)

        return "250 OK"

    async def handle_RCPT(self, server, session, envelope, address, rcpt_options):
        if not address.lower().endswith('@' + HOSTNAME.lower()):
            return "550 Not relaying to this domain"
        
        envelope.rcpt_tos.append(address)
        
        return "250 OK"

    async def handle_DATA(self, server, session, envelope):
        message = message_from_bytes(envelope.content)

        dkim = "dkim=pass" in message.get("Authentication-Results", "")
        spf = "Pass" in message.get("Received-SPF", "")
        
        default_triggered = False

        for recipient in envelope.rcpt_tos:
            for handler in self.handlers:
                if handler.process(recipient, message, dkim, spf):
                    break
            else:
                if not default_triggered and self.default_handler is not None:
                    default_triggered = True
                    self.default_handler(message, dkim, spf)

        return "250 Message accepted for delivery"

