# TorrenterBot
All-in-one Telegram bot and RSS feed generator for automating torrent downloads.

## Features
- Search for torrents using Telegram on [snowfl.com](snowfl.com).
- Integrated HTTP server for RSS feed generation. Use with your favorite BitTorrent client.
- Notification on download completion.

## Demo
<p align="center">
  <img src="demo.gif" style="width: 200px"/>
</p>

## Usage
1. Install Telegram from your phone store, create a new bot using [BotFather](https://t.me/BotFather), and copy the bot token.
2. Clone this repository on the machine running your torrent client.
3. Create `config.json` from the provided template and make the following changes:
   - Add the bot token to the `"TOKEN"` key.
   - Change the `"PORT"` to whichever port number to run the RSS feed server on.
   - Add the names of required RSS feeds under `"RSS_FEEDS"`.
   - Change `"NUM_RESULTS"` to the number of search results the bot should respond with.
4. Run the program using `python main.py`.
5. On the Telegram app, message your newly created bot using `/torrent <query>` to test things out.
6. Once you add a torrent, check the RSS feed on `http://localhost:<PORT>/feed_name` to see if it shows up. Add this URL to your BitTorrent client RSS feeds. 
7. You can configure different download directories for different feeds.
