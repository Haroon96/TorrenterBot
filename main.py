import telebot
from message_handler import MessageHandler
import json
from threading import Thread
import rss_server
import requests

class TelegramBot:
    def __init__(self, token, rss_feeds, rss_api, num_results, allowed_chat_ids, qbittorrent_credentials):    
        self.bot = telebot.TeleBot(token)
        self.rss_feeds = rss_feeds
        self.rss_api = rss_api
        self.num_results = num_results
        self.allowed_chat_ids = allowed_chat_ids
        self.qbittorrent_credentials = qbittorrent_credentials
        self.handlers = {}

    def bot_message_handler(self, messages: list[telebot.types.Message]):
        for message in messages:

            # see who sent this message
            from_user = message.from_user.username
            chat_id = message.chat.id

            # check if chat allowed
            if chat_id not in self.allowed_chat_ids:
                continue

            # check if status message
            if message.text.startswith('/status'):
                api_url = self.qbittorrent_credentials['API_URL']
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
                }
                with requests.Session() as session:
                    data = 'username=%s&password=%s' % (self.qbittorrent_credentials['USERNAME'], self.qbittorrent_credentials['PASSWORD'])
                    session.post(f'{api_url}/auth/login', data=data, headers=headers)
                    req = session.get(f'{api_url}/sync/maindata?rid=0')
                    response = req.json()
                    reply = []
                    print(response)
                    for torrent in response.get('torrents', []).values():
                        reply.append(f'<strong>{torrent["name"]}</strong>\nProgress: {torrent["progress"] * 100:.1f}%')
                    self.bot.send_message(chat_id, '\n\n'.join(reply), parse_mode='HTML')
                    continue


            # check if starting a new session
            if message.text.startswith('/torrent'):
                # check if already in a session with this user and wrap that up
                if from_user in self.handlers and not self.handlers[from_user].is_finished():
                    self.handlers[from_user].finished = True
                self.handlers[from_user] = MessageHandler(self.bot, chat_id, self.rss_api, self.rss_feeds, self.num_results)
                self.handlers[from_user].start()

            # put message in handler queue
            if from_user in self.handlers and not self.handlers[from_user].is_finished():
                self.handlers[from_user].put(message)

    def start(self):
        while True:
            try:
                updates = self.bot.get_updates()
                for update in updates:
                    self.bot_message_handler(update.message)
            except:
                continue

if __name__ == '__main__':

    # load configuration
    with open('config.json') as f:
        config = json.load(f)

    # start rss server
    rss_server_thread = Thread(target=rss_server.start, args=(config["RSS_PORT"],))
    rss_server_thread.start()

    # start bot
    rss_api_url = f'http://localhost:{config["RSS_PORT"]}'
    if config.get("TELEGRAM_API_URL", None):
        telebot.apihelper.API_URL = config.get("TELEGRAM_API_URL")
    bot = TelegramBot(config["TOKEN"], config["RSS_FEEDS"], rss_api_url, config["NUM_RESULTS"], config["ALLOWED_CHAT_IDS"], config["QBITTORRENT_NOX"])
    bot.start()
