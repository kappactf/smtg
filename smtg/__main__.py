#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging

from smtg.app import create_controller
from smtg.handler import MailHandler
from smtg.telegram import create_bot, TelegramRoute

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] in %(module)s:%(lineno)s: %(message)s",
    level=logging.INFO
)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    bot = create_bot(loop)
    route = TelegramRoute(bot)
    handler = MailHandler(loop)
    handler.add_route(route)

    controller = create_controller(handler, loop)
    controller.begin()

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(bot.close())
        controller.end()
        loop.stop()
        loop.close()
