import sys
import telebot
import os
import json
from argparse import ArgumentParser

def main(args):
    # get chat id for this torrent id
    with open('torrent_user_map.csv') as f:
        mapping = f.read().split('\n')
    chat_id = [row for row in mapping if row.startswith(args.id.lower())][0].split(',')[1]

    # read token from config
    with open(os.path.join(os.path.realpath(os.path.dirname(__file__)), 'config.json')) as f:
        config = json.load(f)

    # create bot
    bot = telebot.TeleBot(config["TOKEN"])

    # send message to user
    bot.send_message(chat_id, '<strong>%s</strong> has finished downloading.' % args.name, parse_mode='HTML')
    
def parse_args():
    parser = ArgumentParser()
    parser.add_argument('--id')
    parser.add_argument('--name')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    main(args)