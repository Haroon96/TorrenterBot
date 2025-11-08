import telebot
from message_handler import MessageHandler
import json
from threading import Thread
import requests
from time import sleep
import rss_server
import typing
import plex_wrapper
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

            logger.info(f"Received message from {from_user} ({chat_id}): {message.text}")

            # check if status message
            if message.text.startswith('/status'):
                api_url = self.qbittorrent_credentials['API_URL']
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
                }
                with requests.Session() as session:
                    logger.info("Fetching qBittorrent status")
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
                logger.info(f"Starting new torrent session for user {from_user}")
                # check if already in a session with this user and wrap that up
                if from_user in self.handlers and not self.handlers[from_user].is_finished():
                    self.handlers[from_user].state = MessageHandler.State.FINISHED
                self.handlers[from_user] = MessageHandler(self.bot, chat_id, self.rss_api, self.rss_feeds, self.num_results)
                self.handlers[from_user].start()

            if message.text.startswith('/delete'):
                logger.info(f"Starting new delete session for user {from_user}")
                self.handlers[from_user] = MessageHandler(self.bot, chat_id, self.rss_api, self.rss_feeds, self.num_results)
                self.handlers[from_user].start()

            if message.text.startswith('/rescan'):
                logger.info(f"Rescanning Plex library as requested by user {from_user}")
                plex_wrapper.refresh_library()
                self.bot.send_message(chat_id, "Plex library rescan complete.", reply_to_message_id=message.id)
                continue

            # put message in handler queue
            if from_user in self.handlers and not self.handlers[from_user].is_finished():
                logger.info(f"Forwarding message from {from_user} to their active handler")
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
                        logger.info(f"Handler for user {key} finished, removing from active handlers.")
                        del self.handlers[key]

                # check for new messages
                logger.info("Checking for new updates from Telegram")
                updates = self.bot.get_updates(offset=update_id)
                logger.info(f"Received {len(updates)} new updates")

                # new updates, process accordingly
                if updates:
                    # get latest update_id
                    update_id = updates[-1].update_id + 1
                    
                    # forward to bot handler
                    self.bot_message_handler([upd.message for upd in updates])
            except KeyboardInterrupt:
                break
            except Exception:
                logger.error("Error in main bot loop", exc_info=True)
                sleep(5)
                continue

if __name__ == '__main__':

    # telebot configuration
    telebot.apihelper.RETRY_ON_ERROR = True

    # load configuration
    logger.info("Loading configuration from config.json")
    with open('config.json') as f:
        config = json.load(f)

    # start rss server
    logger.info("Starting RSS server")
    rss_server_thread = Thread(target=rss_server.start, args=(config["RSS_PORT"],))
    rss_server_thread.start()

    # start bot
    logger.info("Starting Telegram bot")
    rss_api_url = f'http://localhost:{config["RSS_PORT"]}'
    if config.get("TELEGRAM_API_URL", None):
        telebot.apihelper.API_URL = config.get("TELEGRAM_API_URL")
    bot = TelegramBot(config["TOKEN"], config["RSS_FEEDS"], rss_api_url, config["NUM_RESULTS"], config["ALLOWED_CHAT_IDS"], config["QBITTORRENT_NOX"])
    bot.start()
