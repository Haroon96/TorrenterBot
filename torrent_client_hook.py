import sys
import telebot
import os
import json

def get_realpath(file):
    return os.path.join(os.path.realpath(os.path.dirname(__file__)), file)

def main(torrent_id, torrent_name):
    # get chat id for this torrent id
    with open(get_realpath('torrent_user_map.csv')) as f:
        mapping = f.read().split('\n')

    # read token from config
    with open(get_realpath('config.json')) as f:
        config = json.load(f)

    try:
        torrent_id, chat_id, name = [row for row in mapping if row.startswith(torrent_id.lower())][0].split(':')
    except:
        torrent_id, chat_id, name = torrent_id, config["DEFAULT_CHAT_ID"], torrent_name

    # create bot
    bot = telebot.TeleBot(config["TOKEN"])

    # send message to user
    bot.send_message(chat_id, '<strong>%s</strong> has finished downloading.' % name, parse_mode='HTML')
    
if __name__ == '__main__':
    telebot.apihelper.RETRY_ON_ERROR = True
    main(sys.argv[1], sys.argv[2])
