# TorrenterBot
All-in-one Telegram bot and RSS feed generator for automating torrent downloads. The program allows searching for torrents and adding them to a built-in RSS feed which any decent BitTorrent client can then read and auto-download from. 

## Features
- Search for torrents using Telegram on [snowfl.com](https://snowfl.com).
- Integrated HTTP server for RSS feed generation. Use with your favorite BitTorrent client.
- Notification on download completion.

## Demo
<p align="center">
  <img src="demo.gif" style="width: 200px"/>
</p>

## Setting up
### Telegram Bot
1. Install Telegram from your phone's app store, create a new bot using [BotFather](https://t.me/BotFather), and copy the bot token.
2. Start a chat with the newly created bot.

### Configuration
1. Create `config.json` from the provided template file `config.json.template`.
2. Add the bot token to the `"TOKEN"` key.
3. Change the `"PORT"` to whichever port number to run the RSS feed server on.
4. Add the names of required RSS feeds under `"RSS_FEEDS"`.
5. Change `"NUM_RESULTS"` to the number of search results the bot should respond with.
5. Change `"DEFAULT_CHAT_ID"` to the default chat ID that should receive notification if download was manually started.

### RSS Feed
1. Start the bot and RSS feed server using `python main.py`.
2. On the Telegram app, message your newly created bot using `/torrent <query>` to test things out.
3. Once you add a torrent, check the RSS feed on `http://localhost:<PORT>/feed_name` to see if it shows up. 
4. Add this URL to your BitTorrent client RSS feeds to auto-download from. 
5. You can configure different download directories for different feeds among other parameters. (Read about how to do this in qBittorrent [here](https://thewiki.moe/tutorials/rss/)).


### Completion Notification
1. Find the option in your BitTorrent client for running external programs on torrent completion.
2. Set the option to run the following command: `python3 <path-to-folder>/torrent_client_hook.py "<torrent-id>" "<torrent-name>"`. For example, in qBittorrent, the command is `python3 torrent_client_hook.py "%K" "%N"`.
