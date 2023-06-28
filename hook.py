import sys
import telebot
import os
import json

def get_realpath(file):
    return os.path.join(os.path.realpath(os.path.dirname(__file__)), file)

def main(torrent_id):
    # get chat id for this torrent id
    with open(get_realpath('torrent_user_map.csv')) as f:
        mapping = f.read().split('\n')
    torrent_id, chat_id, name  = [row for row in mapping if row.startswith(torrent_id.lower())][0].split(':')

    # read token from config
    with open(get_realpath('config.json')) as f:
        config = json.load(f)

    # create bot
    bot = telebot.TeleBot(config["TOKEN"])

    # send message to user
    bot.send_message(chat_id, '<strong>%s</strong> has finished downloading.' % name, parse_mode='HTML')
    
if __name__ == '__main__':
    main(sys.argv[1])