import sys
import telebot
import os
import json

def get_realpath(file):
    return os.path.join(os.path.realpath(os.path.dirname(__file__)), file)

def main(torrent_id, torrent_name):
    # get chat id for this torrent id
    with open(get_realpath('torrent_mappings.tsv')) as f:
        mapping = f.read().split('\n')

    # read token from config
    with open(get_realpath('config.json')) as f:
        config = json.load(f)

    # create bot
    bot = telebot.TeleBot(config["TOKEN"])

    # find users waiting on this torrent including default chat id
    notify_users = set()
    notify_users.add(config['DEFAULT_CHAT_ID'])
    notify_users |= set([int(row.split('\t')[1]) for row in mapping if row.startswith(torrent_id)])

    # send messages to users
    for chat_id in notify_users:
        bot.send_message(chat_id, f'<strong>"{torrent_name}"</strong> has finished downloading.', parse_mode='HTML')
    
if __name__ == '__main__':
    telebot.apihelper.RETRY_ON_ERROR = True
    main(sys.argv[1], sys.argv[2])
