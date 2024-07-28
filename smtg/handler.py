import logging
import uuid
from asyncio import AbstractEventLoop
from datetime import datetime
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser, Parser
from typing import Awaitable, Callable, TypeAlias

import dkim.asyncsupport as dkim
import pydnsbl
import spf
from aiosmtpd.handlers import AsyncMessage
from aiosmtpd.smtp import Envelope, SMTP, Session
from pydnsbl.checker import DNSBLResult
from pydnsbl.providers import BASE_PROVIDERS, ZenSpamhaus

from smtg.config import config

logger = logging.getLogger(__name__)

MailRoute: TypeAlias = Callable[[list[str], EmailMessage], Awaitable[list[str]]]


class MailHandler(AsyncMessage):
    routes: list[MailRoute]

    def __init__(self, loop: AbstractEventLoop):
        providers = [
            provider
            for provider in BASE_PROVIDERS
            if provider.host not in ["cbl.abuseat.org", "zen.spamhaus.org"]
        ]
        if config.spam.dnsbl:
            providers.append(ZenSpamhaus(config.spam.dnsbl))

        self.ip_checker = pydnsbl.DNSBLIpChecker(providers=providers, loop=loop)
        self.routes = []
        self.bytes_parser = BytesParser(policy=policy.default)
        self.string_parser = Parser(policy=policy.default)

        super().__init__()

    def add_route(self, route: MailRoute) -> None:
        """Given route should be a callable accepting two arguments:
          recipients: list[str]   intended recipients of the e-mail
          message: Message        the raw message received

        It should return a list of strings - recipients that should be
        processed by the next rules.

        When no recipients remaining, processing is over.
        """
        self.routes.append(route)

    async def handle_RCPT(self, _server: SMTP, _session: Session, envelope: Envelope, address: str, rcpt_options: list[str]) -> str:
        if not address.lower().endswith(f"@{config.hostname.lower()}"):
            return f"553 Mailbox {address} does not exist"

        envelope.rcpt_tos.append(address)
        envelope.rcpt_options.extend(rcpt_options)

        return "250 OK"

    def prepare_message(self, session: Session, envelope: Envelope) -> EmailMessage:
        data = envelope.content
        message: EmailMessage
        if isinstance(data, (bytes, bytearray)):
            message = BytesParser(policy=policy.default).parsebytes(data)  # type: ignore
        elif isinstance(data, str):
            message = Parser(policy=policy.default).parsestr(data)  # type: ignore
        else:
            raise TypeError(f"Expected str or bytes, got {type(data)}")
        assert isinstance(message, EmailMessage)

        message["X-Smtg-Sender-Hostname"] = session.host_name
        message["X-Smtg-Mail-From"] = envelope.mail_from
        message["X-Smtg-Rcpt-To"] = ",".join(envelope.rcpt_tos)
        if isinstance(session.peer, tuple):
            message["X-Smtg-Peer"] = session.peer[0]
        else:
            message["X-Smtg-Peer"] = session.peer

        return message

    async def handle_message(self, message: EmailMessage) -> None:
        message_id = str(uuid.uuid4())

        spf_result, spf_description = spf.check2(message["X-Smtg-Peer"], message["X-Smtg-Mail-From"], message["X-Smtg-Sender-Hostname"])

        try:
            dkim_result = await dkim.verify_async(message.as_bytes())
        except TypeError:
            dkim_result = False

        ip_check: DNSBLResult = await self.ip_checker.check_async(message["X-Smtg-Peer"])
        is_spam = config.spam.dnsbl and config.spam.dnsbl in ip_check.detected_by.keys() or len(ip_check.detected_by) > 2

        message["X-Smtg-Id"] = message_id
        message["X-SPF-Check"] = spf_result
        message["X-SPF-Check-Details"] = spf_description
        message["X-DKIM-Check"] = "pass" if dkim_result else "fail"
        message["X-DNSBL"] = f"{'pass' if is_spam else 'fail'};detected_by={','.join(ip_check.detected_by.keys())}"

        (config.eml_path / datetime.now().strftime("%Y-%m-%d")).mkdir(parents=True, exist_ok=True)

        with (config.eml_path / datetime.now().strftime("%Y-%m-%d") / f"{message_id}.eml").open(mode="wb") as email_file:
            email_file.write(message.as_bytes())

        if is_spam or spf_result == "fail":
            # We got spam here.
            logger.info("Message %s rejected as spam", message_id)
            return
        logger.info("Message %s accepted", message_id)

        recipients = message["X-Smtg-Rcpt-To"].split(",")

        for route in self.routes:
            recipients = await route(recipients, message)
            if len(recipients) == 0:
                # Nowhere to deliver, exiting.
                return


__all__ = ["MailHandler"]
