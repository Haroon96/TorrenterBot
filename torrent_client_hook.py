import sys
import telebot
import os
import json
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description='Torrent Client Hook for notifying Telegram users on download completion.')
    parser.add_argument('torrent_id', type=str, help='The ID of the completed torrent.')
    parser.add_argument('torrent_name', type=str, help='The name of the completed torrent.')
    return parser.parse_args()

def get_realpath(file):
    return os.path.join(os.path.realpath(os.path.dirname(__file__)), file)

def notify_user_of_completion(torrent_id, torrent_name, config):
    # get chat id for this torrent id
    with open(get_realpath('torrent_mappings.tsv')) as f:
        mapping = f.read().split('\n')

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
    # read in configuration
    with open(get_realpath('config.json')) as f:
        config = json.load(f)
    
    # configure telebot proxy
    if config.get("TELEGRAM_API_URL", None):
        telebot.apihelper.API_URL = config.get("TELEGRAM_API_URL")
    telebot.apihelper.RETRY_ON_ERROR = True

    # parse arguments for torrent
    args = parse_args()
    notify_user_of_completion(args.torrent_id, args.torrent_name, config)
