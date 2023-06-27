from bot import TelegramBot
import json
from threading import Thread
from rss_server import start_server


def main():
    # load configuration
    with open('config.json') as f:
        config = json.load(f)

    # start rss server
    Thread(target=start_server, args=(config["PORT"],)).start()

    # start bot
    bot = TelegramBot(config["TOKEN"], config["RSS_FEEDS"], f'http://localhost:{config["PORT"]}')
    bot.start()

if __name__ == '__main__':
    main()