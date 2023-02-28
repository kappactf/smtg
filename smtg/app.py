import ssl
from asyncio import AbstractEventLoop

from aiosmtpd.controller import UnthreadedController

from smtg.config import config


def create_controller(handler: object, loop: AbstractEventLoop) -> UnthreadedController:
    if config.smtp.tls:
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain(config.smtp.tls.cert_path, config.smtp.tls.key_path, config.smtp.tls.key_passphrase)
    else:
        ssl_context = None

    controller = UnthreadedController(handler, config.smtp.host, config.smtp.port, loop, ssl_context=ssl_context)

    return controller


__all__ = ["create_controller"]
