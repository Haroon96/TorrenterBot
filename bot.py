import telebot
from torrent_handler import TorrentHandler

class TelegramBot:
    def __init__(self, token, rss_feeds, rss_api):    
        self.bot = telebot.TeleBot(token)
        self.rss_feeds = rss_feeds
        self.rss_api = rss_api
        self.handlers = {}

    def bot_message_handler(self, messages: list[telebot.types.Message]):
        for message in messages:
            # see who sent this message
            from_user = message.from_user.username

            # check if starting a new session
            if message.text.startswith('/torrent'):
                # check if already in a session with this user and wrap that up
                if from_user in self.handlers and not self.handlers[from_user].finished:
                    self.handlers[from_user].finished = True
                self.handlers[from_user] = TorrentHandler(self.bot, message.chat.id, self.rss_api, self.rss_feeds)
                self.handlers[from_user].start()
            
            # put message in handler queue
            if from_user in self.handlers and not self.handlers[from_user].finished:
                self.handlers[from_user].put(message)

    def start(self):
        self.bot.set_update_listener(self.bot_message_handler)
        self.bot.infinity_polling()