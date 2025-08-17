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
import urllib.parse

Torrent = namedtuple('Torrent', ['name', 'magnet', 'stats'])

class MessageHandler:

    class State(Enum):
        INITIAL = 1
        TORRENT_SELECTION = 2
        RSS_FEED_SELECTION = 3
        MAGNET_RSS_FEED_SELECTION = 4
        FINISHED = 5

    def __init__(self, bot, chat_id, rss_api, rss_feeds, num_results):
        self.bot = bot
        self.chat_id = chat_id
        self.rss_api = rss_api
        self.rss_feeds = rss_feeds
        self.num_results = num_results
        self.magnet_info = {"link": None, "name": None}
        
        self.queue = Queue()
        self.results = []
        self.state = MessageHandler.State.INITIAL

    def start(self):
        Thread(target=self.handle).start()

    def put(self, message):
        self.queue.put(message)

    def send_message(self, text, reply_to_message_id=None, reply_markup=telebot.types.ReplyKeyboardRemove()):
        if self.is_finished():
            return
        self.bot.send_message(self.chat_id, text, reply_markup=reply_markup, parse_mode='HTML', reply_to_message_id=reply_to_message_id)
    
    def is_finished(self):
        return self.state == MessageHandler.State.FINISHED

    def handle(self):
        while not self.is_finished():
            # get message from queue
            try: 
                message: telebot.types.Message = self.queue.get(timeout=120)
            except Empty:
                if self.state != MessageHandler.State.FINISHED:
                    self.send_message('Your session timed out.')
                    self.state = MessageHandler.State.FINISHED
                continue
                
            if self.state == MessageHandler.State.INITIAL:
                # extract query from message
                query = message.text.replace('/torrent', '').strip()

                if query == '':
                    self.send_message('No query specified.')
                    self.state = MessageHandler.State.FINISHED
                    continue

                if query.startswith('magnet:?'):
                    self.magnet_info["link"] = query
                    match = re.search(r'&dn=([^&]+)', query)
                    self.magnet_info["name"] = urllib.parse.unquote_plus(match.group(1)) if match else "Unknown"
                    self.send_message(
                        f'You sent a magnet link for: <strong>"{self.magnet_info["name"]}"</strong>\n\nSelect RSS feed to add.',
                        reply_to_message_id=message.id,
                        reply_markup=self.build_keyboard_markup(options=self.rss_feeds)
                    )
                    self.state = MessageHandler.State.MAGNET_RSS_FEED_SELECTION
                    continue

                # search for query
                self.send_message(f'Searching for <strong>"{query}"</strong>', reply_to_message_id=message.id)
                self.results = self.search(query)
                
                # check if results not found
                if len(self.results) == 0:
                    self.send_message('No results found! Please try a different query.', reply_to_message_id=message.id)
                    self.state = MessageHandler.State.FINISHED
                    continue

                # show results message
                torrent_results = [f'{i}\n{r.name}\n{r.stats}' for i, r in enumerate(self.results, start=1)]
                torrent_results_message = '\n\n'.join(torrent_results)

                # reply markup is index of torrent
                reply_markup = self.build_keyboard_markup(options=range(1, len(self.results) + 1))

                # send message
                self.send_message(torrent_results_message, reply_markup=reply_markup, reply_to_message_id=message.id)
                self.state = MessageHandler.State.TORRENT_SELECTION
            
            elif self.state == MessageHandler.State.TORRENT_SELECTION:
                # check if valid index
                try: 
                    index = int(message.text) - 1
                except:
                    self.send_message('Invalid!', reply_to_message_id=message.id)
                    continue

                # check if within bounds
                if index < 0 or index > len(self.results):
                    self.send_message('Invalid!', reply_to_message_id=message.id)
                    continue

                # prompt for download
                name = self.results[index].name
                reply_markup = self.build_keyboard_markup(options=self.rss_feeds)
                self.send_message(f'Downloading: <strong>"{name}"</strong>', reply_to_message_id=message.id)
                self.send_message('RSS feed?', reply_markup=reply_markup)                
                self.state = MessageHandler.State.RSS_FEED_SELECTION

            elif self.state == MessageHandler.State.RSS_FEED_SELECTION:
                # check if valid index
                if message.text not in self.rss_feeds:
                    self.send_message('Invalid!', reply_to_message_id=message.id)
                    continue
                
                # send to rss feed
                torrent: Torrent = self.results[index]
                data = dict(name=torrent.name, magnet=torrent.magnet, guid=uuid4().hex)
                requests.post(f'{self.rss_api}/{message.text}', data=json.dumps(data))

                # save user info for later hook
                torrent_id = re.search(r'urn:btih:(.*?)&', torrent.magnet).group(1).lower()
                with open('torrent_mappings.tsv', 'a') as f:
                    f.write(f'{torrent_id}\t{self.chat_id}\t{torrent.name}\n')

                # inform user and finish thread
                self.send_message(f'Added to RSS feed: <strong>"{message.text}"</strong>', reply_to_message_id=message.id)
                self.state = MessageHandler.State.FINISHED
            elif self.state == MessageHandler.State.MAGNET_RSS_FEED_SELECTION:
                if message.text not in self.rss_feeds:
                    self.send_message('Invalid RSS feed!', reply_to_message_id=message.id)
                    continue
                # Add magnet to selected RSS feed
                data = dict(name=self.magnet_info["name"], magnet=self.magnet_info["link"], guid=uuid4().hex)
                requests.post(f'{self.rss_api}/{message.text}', data=json.dumps(data))
                self.send_message(
                    f'Added <strong>"{self.magnet_info["name"]}"</strong> to RSS feed: <strong>"{message.text}"</strong>',
                    reply_to_message_id=message.id
                )
                self.state = MessageHandler.State.FINISHED
                continue

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
            seeds, leeches, size = item['seeder'], item['leecher'], item['size']
            torrent = Torrent(item['name'], item['magnet'], f'S: {seeds}, L: {leeches}, {size}')
            results.append(torrent)
        return results

    def build_keyboard_markup(self, options):
        markup = telebot.types.ReplyKeyboardMarkup()
        # add options as keyboard buttons
        for option in options:
            button = telebot.types.KeyboardButton(option)
            markup.add(button)
        return markup
