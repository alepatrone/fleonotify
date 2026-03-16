import os
import json
import requests
from datetime import datetime, timedelta
from flask import Flask, request
from threading import Thread
import time
import sqlite3

app = Flask(__name__)

# Configuration
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TWITCH_CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')
TWITCH_ACCESS_TOKEN = os.getenv('TWITCH_ACCESS_TOKEN')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')  # e.g., https://your-app.onrender.com

DB_PATH = 'bot_data.db'

# Initialize database
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            chat_id INTEGER,
            platform TEXT,
            channel_name TEXT,
            channel_id TEXT,
            PRIMARY KEY (chat_id, platform, channel_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stream_status (
            platform TEXT,
            channel_id TEXT,
            is_live INTEGER DEFAULT 0,
            last_checked TIMESTAMP,
            PRIMARY KEY (platform, channel_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS youtube_videos (
            video_id TEXT PRIMARY KEY,
            channel_id TEXT,
            title TEXT,
            notified INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Database helpers
def add_subscription(chat_id, platform, channel_name, channel_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO subscriptions (chat_id, platform, channel_name, channel_id)
        VALUES (?, ?, ?, ?)
    ''', (chat_id, platform, channel_name, channel_id))
    conn.commit()
    conn.close()

def remove_subscription(chat_id, platform, channel_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM subscriptions
        WHERE chat_id = ? AND platform = ? AND channel_id = ?
    ''', (chat_id, platform, channel_id))
    conn.commit()
    conn.close()

def get_user_subscriptions(chat_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT platform, channel_name, channel_id FROM subscriptions WHERE chat_id = ?', (chat_id,))
    subs = cursor.fetchall()
    conn.close()
    return subs

def get_all_subscriptions():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT platform, channel_id FROM subscriptions')
    subs = cursor.fetchall()
    conn.close()
    return subs

def update_stream_status(platform, channel_id, is_live):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO stream_status (platform, channel_id, is_live, last_checked)
        VALUES (?, ?, ?, datetime('now'))
    ''', (platform, channel_id, is_live))
    conn.commit()
    conn.close()

def get_stream_status(platform, channel_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT is_live FROM stream_status WHERE platform = ? AND channel_id = ?', 
                   (platform, channel_id))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def get_subscribed_users(platform, channel_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT chat_id FROM subscriptions WHERE platform = ? AND channel_id = ?',
                   (platform, channel_id))
    users = cursor.fetchall()
    conn.close()
    return [u[0] for u in users]

# Telegram API helpers
def send_message(chat_id, text):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}
    requests.post(url, json=payload)

def send_message_with_button(chat_id, text, url):
    telegram_url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML',
        'reply_markup': json.dumps({
            'inline_keyboard': [[{
                'text': '🔴 Watch Stream',
                'url': url
            }]]
        })
    }
    requests.post(telegram_url, json=payload)

# Twitch API
def get_twitch_user_id(channel_name):
    """Get user ID from channel name"""
    headers = {
        'Client-ID': TWITCH_CLIENT_ID,
        'Authorization': f'Bearer {TWITCH_ACCESS_TOKEN}'
    }
    url = f'https://api.twitch.tv/helix/users?login={channel_name}'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data['data']:
            return data['data'][0]['id']
    return None

def check_twitch_live(channel_id, channel_name):
    """Check if Twitch channel is currently live"""
    headers = {
        'Client-ID': TWITCH_CLIENT_ID,
        'Authorization': f'Bearer {TWITCH_ACCESS_TOKEN}'
    }
    url = f'https://api.twitch.tv/helix/streams?user_id={channel_id}'
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data['data']:
            stream = data['data'][0]
            return True, stream['title'], f'https://twitch.tv/{channel_name}'
    return False, None, None

# YouTube API
def get_youtube_channel_id(channel_name):
    """Get YouTube channel ID from channel name/handle"""
    url = 'https://www.googleapis.com/youtube/v3/search'
    params = {
        'q': channel_name,
        'part': 'snippet',
        'type': 'channel',
        'key': YOUTUBE_API_KEY,
        'maxResults': 1
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data.get('items'):
            return data['items'][0]['snippet']['channelId']
    return None

def check_youtube_new_videos(channel_id, channel_name):
    """Check for new YouTube videos from a channel"""
    url = 'https://www.googleapis.com/youtube/v3/search'
    params = {
        'channelId': channel_id,
        'part': 'snippet',
        'type': 'video',
        'order': 'date',
        'key': YOUTUBE_API_KEY,
        'maxResults': 3
    }
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        new_videos = []
        
        if data.get('items'):
            for item in data['items']:
                video_id = item['id']['videoId']
                title = item['snippet']['title']
                
                # Check if we already notified about this video
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute('SELECT notified FROM youtube_videos WHERE video_id = ?', (video_id,))
                result = cursor.fetchone()
                
                if result is None or result[0] == 0:
                    new_videos.append({
                        'id': video_id,
                        'title': title,
                        'url': f'https://www.youtube.com/watch?v={video_id}'
                    })
                    # Mark as notified
                    cursor.execute('''
                        INSERT OR REPLACE INTO youtube_videos (video_id, channel_id, title, notified)
                        VALUES (?, ?, ?, 1)
                    ''', (video_id, channel_id, title))
                
                conn.commit()
                conn.close()
        
        return new_videos
    return []

# Background monitoring
def monitor_channels():
    """Continuously monitor channels for live streams and new videos"""
    while True:
        try:
            subscriptions = get_all_subscriptions()
            
            for platform, channel_id in subscriptions:
                if platform == 'twitch':
                    # Get channel name from subscriptions
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute('SELECT channel_name FROM subscriptions WHERE platform = ? AND channel_id = ? LIMIT 1',
                                   (platform, channel_id))
                    result = cursor.fetchone()
                    conn.close()
                    
                    if result:
                        channel_name = result[0]
                        is_live, title, stream_url = check_twitch_live(channel_id, channel_name)
                        was_live = get_stream_status(platform, channel_id)
                        
                        # Stream just went live
                        if is_live and not was_live:
                            update_stream_status(platform, channel_id, 1)
                            users = get_subscribed_users(platform, channel_id)
                            for user_id in users:
                                send_message_with_button(
                                    user_id,
                                    f'🔴 <b>{channel_name}</b> is now live!\n\n<i>{title}</i>',
                                    stream_url
                                )
                        
                        # Stream went offline
                        elif not is_live and was_live:
                            update_stream_status(platform, channel_id, 0)
                
                elif platform == 'youtube':
                    # Get channel name from subscriptions
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute('SELECT channel_name FROM subscriptions WHERE platform = ? AND channel_id = ? LIMIT 1',
                                   (platform, channel_id))
                    result = cursor.fetchone()
                    conn.close()
                    
                    if result:
                        channel_name = result[0]
                        new_videos = check_youtube_new_videos(channel_id, channel_name)
                        
                        if new_videos:
                            users = get_subscribed_users(platform, channel_id)
                            for user_id in users:
                                for video in new_videos:
                                    send_message_with_button(
                                        user_id,
                                        f'🎬 <b>{channel_name}</b> posted a new video!\n\n<i>{video["title"]}</i>',
                                        video['url']
                                    )
            
            # Check every 5 minutes
            time.sleep(300)
        
        except Exception as e:
            print(f'Error in monitor_channels: {e}')
            time.sleep(60)

# Telegram bot handlers
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        
        if 'message' in data:
            message = data['message']
            chat_id = message['chat']['id']
            text = message.get('text', '')
            
            if text.startswith('/start'):
                send_message(chat_id, 
                    '👋 Welcome to Twitch & YouTube Notifications Bot!\n\n'
                    'Available commands:\n'
                    '/subscribe_twitch <channel_name> - Subscribe to Twitch channel\n'
                    '/subscribe_youtube <channel_name> - Subscribe to YouTube channel\n'
                    '/list - Show your subscriptions\n'
                    '/unsubscribe <platform> <channel_name> - Unsubscribe'
                )
            
            elif text.startswith('/subscribe_twitch '):
                channel_name = text.replace('/subscribe_twitch ', '').strip().lower()
                channel_id = get_twitch_user_id(channel_name)
                
                if channel_id:
                    add_subscription(chat_id, 'twitch', channel_name, channel_id)
                    send_message(chat_id, f'✅ Subscribed to Twitch channel: <b>{channel_name}</b>')
                else:
                    send_message(chat_id, f'❌ Twitch channel <b>{channel_name}</b> not found')
            
            elif text.startswith('/subscribe_youtube '):
                channel_name = text.replace('/subscribe_youtube ', '').strip()
                channel_id = get_youtube_channel_id(channel_name)
                
                if channel_id:
                    add_subscription(chat_id, 'youtube', channel_name, channel_id)
                    send_message(chat_id, f'✅ Subscribed to YouTube channel: <b>{channel_name}</b>')
                else:
                    send_message(chat_id, f'❌ YouTube channel <b>{channel_name}</b> not found')
            
            elif text == '/list':
                subs = get_user_subscriptions(chat_id)
                if subs:
                    msg = '📋 Your subscriptions:\n\n'
                    for platform, channel_name, channel_id in subs:
                        emoji = '🎮' if platform == 'twitch' else '🎬'
                        msg += f'{emoji} {platform.upper()}: <b>{channel_name}</b>\n'
                    send_message(chat_id, msg)
                else:
                    send_message(chat_id, 'You have no subscriptions yet.')
            
            elif text.startswith('/unsubscribe '):
                parts = text.replace('/unsubscribe ', '').strip().split(' ', 1)
                if len(parts) == 2:
                    platform, channel_name = parts[0].lower(), parts[1]
                    
                    # Get channel ID
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute('SELECT channel_id FROM subscriptions WHERE chat_id = ? AND platform = ? AND channel_name = ?',
                                   (chat_id, platform, channel_name))
                    result = cursor.fetchone()
                    conn.close()
                    
                    if result:
                        channel_id = result[0]
                        remove_subscription(chat_id, platform, channel_id)
                        send_message(chat_id, f'✅ Unsubscribed from {platform.upper()}: <b>{channel_name}</b>')
                    else:
                        send_message(chat_id, f'❌ Subscription not found')
                else:
                    send_message(chat_id, 'Usage: /unsubscribe <platform> <channel_name>')
    
    except Exception as e:
        print(f'Error in webhook: {e}')
    
    return 'ok'

@app.route('/health', methods=['GET'])
def health():
    return 'ok', 200

if __name__ == '__main__':
    # Start background monitoring thread
    monitor_thread = Thread(target=monitor_channels, daemon=True)
    monitor_thread.start()
    
    # Set webhook with Telegram
    if WEBHOOK_URL:
        webhook_route = f'{WEBHOOK_URL}/webhook'
        telegram_url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook'
        requests.post(telegram_url, json={'url': webhook_route})
    
    # Start Flask server
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
