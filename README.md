# SMTG

Asynchronous and fast Python mail server, which can route your messages to Telegram.

## Features

* Spam check
* Saves raw EML to drive so you could check them out
* Telegram formatting (bold, italic, links)
* Attachments support

## Getting Started

#### Bot Setup

Use [@BotFather](https://t.me/BotFather) to create a new bot. You will get a token.

#### Spamhaus Setup

By default, SMTG uses several built-in providers for checking spam. You can use Spamhaus Zen or any DNSBL of your choice.

Message is considered as a spam if sender IP is blacklisted either by your DNSBL or by at least three of built-in providers.

To use Spamhaus Zen, you need to get key. You can get it [here](https://www.spamhaus.org/zen/). For other providers, ask them for domain name.

#### Configuration

Create file `config.toml` in a working directory containing:

```toml
[smtg]
# Your domain name, REQUIRED
hostname = "example.org"
# Path to save EML files, REQUIRED
eml_path = "."

[smtg.spam]
# DNSBL provider domain, OPTIONAL
dnsbl = "yourtoken.zen.dq.spamhaus.net"
# List of forbidden words, OPTIONAL
blacklist = ["i'm spam!!"]

[smtg.telegram]
# Telegram bot token, REQUIRED
token = "YOUR_TOKEN"
# Telegram chat ID for unmatched messages, REQUIRED
catch_all_chat_id = 123456789
# Telegram chat IDs for personal messages, OPTIONAL
inboxes = [
    { chat_id = 987654321, emails = ["important@example.org"] }
]
```

#### Domain Setup

Point MX record to your server.

#### Run

* To install dependencies: `poetry install`.
* To run: `poetry run python -m smtg`.

## Extending

You can use only `smtg.handler.MailHandler` class and implement your own logic for handling messages — personal inboxes, complex rules, different messenger, etc.

## TODO 

- [ ] Outgoing messages (via separate command or reply)
- [ ] Async SPF library
- [ ] Check DMARC

## License

This server is written by [Nikita Sychev](https://nsychev.ru).

You can use this code at your own. All sources are licensed by [MIT License](LICENSE).
