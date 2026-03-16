# Telegram Bot Setup Guide (Render.com)

## Step 1: Get API Keys

### 1.1 Telegram Bot Token
1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Follow the prompts to create a bot
4. Copy the **HTTP API token** (looks like: `123456789:ABCDEFGhijklmnopqrstuvwxyz`)
5. Save it somewhere safe

### 1.2 Twitch API Credentials
1. Go to https://dev.twitch.tv/console/apps
2. Click **Create Application**
   - Name: anything (e.g., "Stream Notifications")
   - Category: "Application Integration"
   - Accept terms and create
3. Click **Manage** on your app
4. Note the **Client ID**
5. Click **New Secret** to generate a secret (save this too)
6. Go to **OAuth** tab
7. Set **OAuth Redirect URL** to: `http://localhost:3000` (doesn't matter for bot)
8. Get your **access token**:
   - Go to https://id.twitch.tv/oauth2/authorize?client_id=YOUR_CLIENT_ID&redirect_uri=http://localhost:3000&response_type=token&scope=
   - Replace YOUR_CLIENT_ID with your actual Client ID
   - Authorize and copy the access token from the URL (`access_token=...`)

**Simpler Twitch token method:**
- Use: https://twitchtokengenerator.com/
- Paste your Client ID and Secret
- Generate token

### 1.3 YouTube API Key
1. Go to https://console.cloud.google.com
2. Create a new project (top left dropdown)
3. Search for **YouTube Data API v3**
4. Click **Enable**
5. Go to **Credentials** → **Create Credentials** → **API Key**
6. Copy the API key

---

## Step 2: Deploy to Render.com

### 2.1 Prepare Your Code
1. Create a GitHub account (if you don't have one)
2. Create a new repository called `telegram-bot`
3. Upload these files to the repo:
   - `bot.py`
   - `requirements.txt`
   - `build.sh`
4. Commit and push

**File structure:**
```
telegram-bot/
├── bot.py
├── requirements.txt
├── build.sh
└── .gitignore (optional, add: bot_data.db)
```

### 2.2 Create Render Service
1. Go to https://render.com
2. Sign up with GitHub (easiest)
3. Click **New +** → **Web Service**
4. Select your `telegram-bot` repository
5. Fill in:
   - **Name:** `telegram-bot` (or your preferred name)
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
   - **Plan:** Free
6. Click **Create Web Service**
7. Wait 2-3 minutes for deployment

### 2.3 Get Your Render URL
Once deployed, you'll see a URL like: `https://your-app-name.onrender.com`
Copy this - you'll need it next.

---

## Step 3: Set Environment Variables

On Render dashboard:
1. Go to your web service
2. Click **Environment** (left sidebar)
3. Add these variables:

```
TELEGRAM_TOKEN = your_telegram_bot_token
TWITCH_CLIENT_ID = your_twitch_client_id
TWITCH_ACCESS_TOKEN = your_twitch_access_token
YOUTUBE_API_KEY = your_youtube_api_key
WEBHOOK_URL = https://your-app-name.onrender.com
PORT = 5000
```

4. Click **Save Changes**
5. The service will auto-redeploy

---

## Step 4: Test Your Bot

1. Open Telegram and search for your bot (the one you created with @BotFather)
2. Send `/start`
3. You should see the welcome message

### Test Commands:
```
/subscribe_twitch ninja
/subscribe_youtube MrBeast
/list
/unsubscribe twitch ninja
```

---

## Step 5: How It Works

### Subscription Storage
- All subscriptions are saved in `bot_data.db` (SQLite)
- Stored on Render's ephemeral filesystem
- **Important:** If you restart the service, data persists (mostly)

### Monitoring Loop
- Bot checks Twitch/YouTube every 5 minutes
- When a channel goes live or posts a video, all subscribers get notified
- Notifications include a direct link button

### Telegram Webhook
- Bot sets a webhook with Telegram
- Telegram sends updates to `/webhook` endpoint
- Commands are processed instantly

---

## Troubleshooting

### Bot doesn't respond to commands
- Check if `TELEGRAM_TOKEN` is correct in Environment variables
- Restart the service: Dashboard → **Restart Service**
- Check logs: Dashboard → **Logs** tab

### Subscriptions disappear after restart
- This is normal on Render's free tier (ephemeral filesystem)
- **Solution:** Use a Render PostgreSQL database (paid) or switch to Railway for persistent storage

### Not getting live notifications
- Verify API keys are correct
- Check the **Logs** tab for errors
- Make sure you're subscribed: `/list`

### Twitch channel not found
- Use the exact channel name (e.g., `ninja`, not `Ninja`)
- Channel names are case-sensitive in Twitch API

### YouTube channel not found
- Try the channel's display name or handle
- If that fails, go to the channel and copy the channel ID from the URL
- Currently bot searches by name, not ID (can be improved)

---

## Optional: Upgrade to Persistent Storage

If you want subscriptions to survive service restarts:

### Option 1: Use Railway (Recommended)
- Switch to Railway instead (they offer free PostgreSQL)
- Modify the bot code to use PostgreSQL instead of SQLite

### Option 2: Add Render PostgreSQL Database
1. Go to Dashboard → **Databases**
2. Create a PostgreSQL database ($7/month)
3. Update bot code to use PostgreSQL

For now, SQLite is fine for testing with a few channels.

---

## Cost Breakdown (Free Tier)

| Service | Cost |
|---------|------|
| Render Web Service | Free ✅ |
| Telegram API | Free ✅ |
| Twitch API (free tier) | Free ✅ |
| YouTube API (free tier) | Free ✅ |
| SQLite Database | Free ✅ |
| **Total** | **$0/month** |

**Note:** Render's free tier has a caveat - the service spins down after 15 minutes of inactivity. This means:
- The monitoring loop will pause
- When someone sends a command, it wakes up (takes ~30 seconds)
- Not ideal for 24/7 monitoring, but acceptable for a hobby bot

If you need 24/7 monitoring without interruptions, upgrade to Render's paid tier ($7/month) or switch to Railway ($5/month).

---

## Next Steps

1. Deploy the bot to Render ✅
2. Set environment variables ✅
3. Test with `/start` and `/subscribe_twitch` ✅
4. Add 1-5 channels you want to monitor
5. Get notified! 🎉

Need help? Check the logs on Render dashboard or reply with any errors you see.
