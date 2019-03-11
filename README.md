# Telegram Mail Server

Easy mail server for your domain, which forwards all messages
to Telegram chat.

## Features

* Supports Telegram formatting (bold, italic, links)

## How-to

You need Python 3 and pip.

Install all dependencies: `pip3 -r requirements.txt`.

Run server: `python3 relay.py`.

Point your domain MX records to your host: `@ IN MX 10 YOUR.HOSTNAME.HERE`.

## TODO 

- [ ] Outgoing messages
- [ ] Basic formatting
- [ ] Telegram reply → Outgoing message
- [ ] Personal inbox

## License

This server is written by [Nikita Sychev](https://nsychev.ru).

You can use code at your own. All sources are licensed by [MIT License](LICENSE).

