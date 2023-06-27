import telebot
from queue import Queue, Empty
from threading import Thread
from collections import namedtuple
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By
from time import sleep
import requests
import json
from uuid import uuid4
import re

Torrent = namedtuple('Torrent', ['name', 'magnet', 'stats'])

class TorrentHandler:
    def __init__(self, bot, chat_id, rss_api, rss_feeds, num_results):
        self.bot: telebot.TeleBot = bot
        self.chat_id = chat_id
        self.rss_api = rss_api
        self.rss_feeds = rss_feeds
        self.num_results = num_results
        self.finished = False
        self.state = 'init'
        self.queue = Queue()
        self.thread = Thread(target=self.handle)
        self.results = []

    def start(self):
        self.thread.start()

    def put(self, message):
        self.queue.put(message)

    def send_message(self, text, reply_markup=telebot.types.ReplyKeyboardRemove()):
        if not self.finished:
            self.bot.send_message(self.chat_id, text, reply_markup=reply_markup, parse_mode='HTML')

    def handle(self):
        while not self.finished:
            # get message from queue
            try: 
                message: telebot.types.Message = self.queue.get(timeout=120)
            except Empty:
                self.send_message('Your session timed out.')
                self.finished = True
                
            if self.state == 'init':
                # extract query from message
                query = message.text.replace('/torrent', '').strip()

                if query == '':
                    self.send_message('No query specified.')
                    self.finished = True
                    continue

                # search for query
                self.send_message('Searching...')
                self.search(query)
                
                # check if results not found
                if len(self.results) == 0:
                    self.send_message('No results found! Please try a different query.')
                    self.finished = True
                    continue

                # show results and ask for input
                message = '\n'.join(['%s\n%s\n' % (r.name, r.stats) for r in self.results])
                self.send_message(message, self.build_markup(self.results, index=True))
                self.state = 'pending_response_1'
            
            elif self.state == 'pending_response_1':
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
                self.send_message('Downloading <strong>%s</strong>' % self.results[index].name)
                self.send_message('RSS feed?', self.build_markup(self.rss_feeds))                
                self.state = 'pending_response_2'

            elif self.state == 'pending_response_2':
                # check if valid index
                if message.text not in self.rss_feeds:
                    self.send_message('Invalid!')
                    continue
                
                # send to rss feed
                torrent: Torrent = self.results[index]
                data = dict(name=torrent.name, magnet=torrent.magnet, guid=uuid4().hex)
                requests.post(f'{self.rss_api}/{message.text}', data=json.dumps(data))

                # save user info for later hook
                torrent_id = re.search(r'urn:btih:(.*?)&', torrent.magnet).group(1)
                with open('torrent_user_map.csv', 'a') as f:
                    f.write('%s,%s\n' % (torrent_id, self.chat_id))

                # inform user and finish thread
                self.send_message("Added to RSS feed <strong>%s</strong>." % message.text)
                self.state = 'finished'
                self.finished = True


    def search(self, query):
        options = ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        driver = Chrome(options=options)

        # get website
        driver.get('https://snowfl.com')
        driver.find_element(By.ID, 'query').send_keys(query)
        sleep(1)
        driver.find_element(By.ID, 'btn-search').click()
        sleep(5)

        # find results
        results = driver.find_elements(By.CLASS_NAME, 'result-item')[:self.num_results]

        # return name and magnet
        for item in results:
            name = item.find_element(By.CLASS_NAME, 'name').text
            magnet = item.find_element(By.CLASS_NAME, 'torrent')
            magnet_link = magnet.get_attribute('href')

            # check if link loaded
            while '#fetch' in magnet_link:
                magnet.click()
                magnet_link = magnet.get_attribute('href')

            seed = item.find_element(By.CLASS_NAME, 'seed').text
            leech = item.find_element(By.CLASS_NAME, 'leech').text
            size = item.find_element(By.CLASS_NAME, 'size').text
            if name.strip() != '':
                self.results.append(Torrent(name, magnet_link, 'S:%s, L:%s, %s' % (seed, leech, size)))

        # close driver
        driver.close()

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
