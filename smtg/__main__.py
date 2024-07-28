#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging

from smtg.app import create_controller
from smtg.config import config
from smtg.handler import MailHandler
from smtg.telegram import create_bot, TelegramRoute

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] in %(module)s:%(lineno)s: %(message)s",
    level=logging.INFO
)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    bot = create_bot()
    handler = MailHandler(loop)

    for inbox in config.telegram.inboxes:
        route = TelegramRoute(bot, inbox.chat_id, inbox.emails)
        handler.add_route(route)

    default_route = TelegramRoute(bot, config.telegram.catch_all_chat_id)
    handler.add_route(default_route)

    controller = create_controller(handler, loop)
    controller.begin()

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(bot.session.close())
        controller.end()
        loop.stop()
        loop.close()
