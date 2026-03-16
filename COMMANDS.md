# Bot Commands Quick Reference

## Basic Commands

### /start
Shows welcome message and available commands.

**Usage:**
```
/start
```

---

## Subscription Commands

### /subscribe_twitch
Subscribe to a Twitch channel and get notified when they go live.

**Usage:**
```
/subscribe_twitch ninja
/subscribe_twitch shroud
/subscribe_twitch pokimane
```

**What you get:**
- Notification when channel goes live
- Stream title
- Direct link to stream

---

### /subscribe_youtube
Subscribe to a YouTube channel and get notified when they upload a new video.

**Usage:**
```
/subscribe_youtube MrBeast
/subscribe_youtube LinusTechTips
/subscribe_youtube PewDiePie
```

**What you get:**
- Notification for new video uploads
- Video title
- Direct link to video

---

### /list
Show all your current subscriptions.

**Usage:**
```
/list
```

**Example output:**
```
📋 Your subscriptions:

🎮 TWITCH: ninja
🎮 TWITCH: shroud
🎬 YOUTUBE: MrBeast
```

---

### /unsubscribe
Unsubscribe from a channel.

**Usage:**
```
/unsubscribe twitch ninja
/unsubscribe youtube MrBeast
```

**Parameters:**
- `platform` - either `twitch` or `youtube`
- `channel_name` - exact name you used when subscribing

---

## How Notifications Work

### Twitch Live Notifications
- Checked every 5 minutes
- Sent instantly when you go live
- Includes: streamer name, stream title, watch button
- Only sent once per stream

### YouTube Upload Notifications
- Checked every 5 minutes
- Sent instantly when you upload
- Includes: channel name, video title, watch button
- Only sent once per video

---

## Troubleshooting

### "Channel not found"
- Check spelling (Twitch: all lowercase, e.g., `ninja` not `Ninja`)
- For YouTube, use the display name or handle

### Notifications not arriving
- Make sure you subscribed: run `/list`
- Check that the channel has actually gone live
- Service might be sleeping on Render free tier (wakes up on activity)

### Want to re-subscribe to a channel?
- First unsubscribe: `/unsubscribe twitch ninja`
- Then re-subscribe: `/subscribe_twitch ninja`

---

## Tips

- You can subscribe to as many channels as you want
- Subscriptions are per-user (not per-chat group)
- Use in group chats or DMs - both work!
- Channel names are case-sensitive for Twitch (must be lowercase)

---

## Example Workflow

1. `/start` - See welcome message
2. `/subscribe_twitch ninja` - Start watching Ninja's Twitch
3. `/subscribe_youtube MrBeast` - Start watching MrBeast's YouTube
4. `/list` - Verify subscriptions
5. **Wait for notifications!** 🔔
6. `/unsubscribe twitch ninja` - Stop watching when done
