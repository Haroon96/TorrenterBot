import requests
import json

class TelegramAPI:
    def __init__(self, api_key, api_url='https://api.telegram.org/bot'):
        self.api_key = api_key
        self.api_url = api_url
        self.update_id = -1

    def send_request(self, method, params):
        r = requests.get(f'{self.api_url}{self.api_key}/{method}', params=params)
        return r.json()

    def send_message(self, chat_id, text, reply_to_message_id=None, parse_mode=None, reply_markup=None):
        # Logic to send a message via Telegram API
        pass

    def get_updates(self):
        updates = self.send_request('getUpdates', {'offset': self.update_id + 1, 'timeout': 10})
        if updates['ok'] and updates['result']:
            result = updates['result']
            self.update_id = result[-1]['update_id']
        return result if updates['ok'] else []
    
if __name__ == '__main__':
    
    with open('config.json') as f:
        config = json.load(f)

    api_key = config['TOKEN']
    bot = TelegramAPI(api_key)#, api_url="https://hamo-telegram-proxy.pages.dev/api/bot{0}/{1}")

    while True:
        updates = bot.get_updates()
        for update in updates:
            print(update)