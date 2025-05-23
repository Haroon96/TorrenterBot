import telebot.types
from queue import Queue, Empty
from threading import Thread
from collections import namedtuple
import requests
import json
from uuid import uuid4
import re
import requests
from time import time
import random
import string
from enum import Enum

Torrent = namedtuple('Torrent', ['name', 'magnet', 'stats'])

class MessageHandler:

    class State(Enum):
        INITIAL = 1
        TORRENT_SELECTION = 2
        RSS_FEED_SELECTION = 3
        FINISHED = 4

    def __init__(self, bot, chat_id, rss_api, rss_feeds, num_results):
        self.bot = bot
        self.chat_id = chat_id
        self.rss_api = rss_api
        self.rss_feeds = rss_feeds
        self.num_results = num_results
        
        self.queue = Queue()
        self.results = []
        self.state = MessageHandler.State.INITIAL

    def start(self):
        Thread(target=self.handle).start()

    def put(self, message):
        self.queue.put(message)

    def send_message(self, text, reply_markup=telebot.types.ReplyKeyboardRemove()):
        if self.state == MessageHandler.State.FINISHED:
            return
        self.bot.send_message(self.chat_id, text, reply_markup=reply_markup, parse_mode='HTML')

    def handle(self):
        while self.state != MessageHandler.State.FINISHED:
            # get message from queue
            try: 
                message: telebot.types.Message = self.queue.get(timeout=120)
            except Empty:
                self.send_message('Your session timed out.')
                self.state = MessageHandler.State.FINISHED
                
            if self.state == MessageHandler.State.INITIAL:
                # extract query from message
                query = message.text.replace('/torrent', '').strip()

                if query == '':
                    self.send_message('No query specified.')
                    self.state = MessageHandler.State.FINISHED
                    continue

                # search for query
                self.send_message('Searching...')
                self.results = self.search(query)
                
                # check if results not found
                if len(self.results) == 0:
                    self.send_message('No results found! Please try a different query.')
                    self.state = MessageHandler.State.FINISHED
                    continue

                # show results and ask for input
                message = '\n'.join(['<strong>%s:</strong> %s\n%s\n' % (i + 1, r.name, r.stats) for i, r in enumerate(self.results)])
                self.send_message(message, self.build_markup(self.results, index=True))
                self.state = MessageHandler.State.TORRENT_SELECTION
            
            elif self.state == MessageHandler.State.TORRENT_SELECTION:
                # check if valid index
                try: 
                    index = int(message.text) - 1
                except:
                    self.send_message('Invalid!')
                    continue

                # check if within bounds
                if index < 0 or index > len(self.results):
                    self.send_message('Invalid!')
                    continue

                # prompt for download
                self.send_message('Downloading: <strong>%s</strong>' % self.results[index].name)
                self.send_message('RSS feed?', self.build_markup(self.rss_feeds))                
                self.state = MessageHandler.State.RSS_FEED_SELECTION

            elif self.state == MessageHandler.State.RSS_FEED_SELECTION:
                # check if valid index
                if message.text not in self.rss_feeds:
                    self.send_message('Invalid!')
                    continue
                
                # send to rss feed
                torrent: Torrent = self.results[index]
                data = dict(name=torrent.name, magnet=torrent.magnet, guid=uuid4().hex)
                requests.post(f'{self.rss_api}/{message.text}', data=json.dumps(data))

                # save user info for later hook
                torrent_id = re.search(r'urn:btih:(.*?)&', torrent.magnet).group(1).lower()
                with open('torrent_user_map.csv', 'a') as f:
                    f.write('%s:%s:%s\n' % (torrent_id, self.chat_id, torrent.name))

                # inform user and finish thread
                self.send_message("Added to RSS feed: <strong>%s</strong>" % message.text)
                self.state = MessageHandler.State.FINISHED


    def search(self, query):
        # get snowfl homepage
        url = 'https://snowfl.com/'
        headers = {'user-agent': 'haroon/torrenterbot'}
        response = requests.get(url, headers=headers)

        # get snowfl token
        src = re.search(r'src="(b.min.js.*?)"', response.text).group(1)
        script = requests.get(url + src, headers=headers).text
        token = re.search(r'"(\w{30,45})"', script).group(1)

        # build query
        random_str = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8))
        query = '{0}/{1}/{2}/{3}/0/SEED/NONE/1?_={4}'.format(url, token, query, random_str, str(int(time() * 1000)))

        # get search results
        r = requests.get(query, headers=headers)
        response = r.json()

        # return name and magnet
        results = []
        for item in response[:self.num_results]:
            if 'magnet' not in item:
                continue
            torrent = Torrent(item['name'], item['magnet'], 'S: %s, L: %s, %s' % (item['seeder'], item['leecher'], item['size']))
            results.append(torrent)
        return results

    def build_markup(self, options, index=False):
        markup = telebot.types.ReplyKeyboardMarkup()
        for i, val in enumerate(options):
            # or add KeyboardButton one row at a time:
            if index:
                button = telebot.types.KeyboardButton(f'{i + 1}')
            else:
                button = telebot.types.KeyboardButton(val)
            markup.add(button)
        return markup
