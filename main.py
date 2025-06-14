import telebot
from message_handler import MessageHandler
import json
from threading import Thread
import requests
from time import sleep
import rss_server
import typing

class TelegramBot:
    def __init__(self, token, rss_feeds, rss_api, num_results, allowed_chat_ids, qbittorrent_credentials):    
        self.bot = telebot.TeleBot(token)
        self.rss_feeds: typing.List[str] = rss_feeds
        self.rss_api: str = rss_api
        self.num_results: int = num_results
        self.allowed_chat_ids: typing.List[int] = allowed_chat_ids
        self.qbittorrent_credentials: typing.Dict[str, str] = qbittorrent_credentials
        self.handlers: typing.Dict[str, MessageHandler] = {}

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
                    username = self.qbittorrent_credentials['USERNAME']
                    password = self.qbittorrent_credentials['PASSWORD']
                    data = f'username={username}&password={password}'
                    session.post(f'{api_url}/auth/login', data=data, headers=headers)
                    req = session.get(f'{api_url}/sync/maindata?rid=0')
                    response = req.json()
                    reply = []
                    for torrent in response.get('torrents', {}).values():
                        reply.append(f'<strong>{torrent["name"]}</strong>\nProgress: {torrent["progress"] * 100:.1f}%')
                    if not reply:
                        reply = ['No torrents in progress']
                    self.bot.send_message(chat_id, '\n\n'.join(reply), parse_mode='HTML', reply_to_message_id=message.id)
                    continue


            # check if starting a new session
            if message.text.startswith('/torrent'):
                # check if already in a session with this user and wrap that up
                if from_user in self.handlers and not self.handlers[from_user].is_finished():
                    self.handlers[from_user].state = MessageHandler.State.FINISHED
                self.handlers[from_user] = MessageHandler(self.bot, chat_id, self.rss_api, self.rss_feeds, self.num_results)
                self.handlers[from_user].start()

            # put message in handler queue
            if from_user in self.handlers and not self.handlers[from_user].is_finished():
                self.handlers[from_user].put(message)

    def start(self):
        update_id = None

        # loop infinitely
        while True:
            try:
                # clear out finished handlers
                keys = list(self.handlers.keys())
                for key in keys:
                    handler = self.handlers[key]
                    if handler.is_finished():
                        del self.handlers[key]

                # check for new messages
                updates = self.bot.get_updates(offset=update_id)

                # new updates, process accordingly
                if updates:
                    # get latest update_id
                    update_id = updates[-1].update_id + 1
                    
                    # forward to bot handler
                    self.bot_message_handler([upd.message for upd in updates])
            except KeyboardInterrupt:
                break
            except Exception:
                sleep(5)
                continue

if __name__ == '__main__':

    # telebot configuration
    telebot.apihelper.RETRY_ON_ERROR = True

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
