# YouTube GIF Telegram Bot

A Telegram bot for creating GIFs from YouTube videos using the yt-dlp-host API.

## Installation

1.  Clone the repository:
    ```bash
    git clone <repository_url>
    cd yt-gif-bot
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  Configure your settings in `config.py`:
    *   `TELEGRAM_BOT_TOKEN` - Your Telegram bot token from @BotFather.
    *   `YT_DLP_HOST_URL` - The URL of your yt-dlp-host server.
    *   `YT_DLP_API_KEY` - The API key for your server (see instructions below).
    *   `BOT_LANGUAGE` - The bot's language. Supported: `"en"` (English), `"ru"` (Russian).
    *   `REQUIRED_CHANNEL_ID` - (Optional) Channel ID for mandatory subscription.
    *   `MAX_GIF_DURATION` - Maximum allowed GIF duration in seconds.

## Creating an API Key for yt-dlp-host

The bot requires an API key with `get_video` and `get_info` permissions.

### Using a Python script:

```python
import yt_dlp_host_api

# Connect to the API with your admin key
api = yt_dlp_host_api.api('http://your-api-url.com')
admin_client = api.get_client('YOUR_ADMIN_API_KEY')

# Create a new key for the bot
new_key = admin_client.create_key(
    name="telegram_bot_key",
    permissions=["get_video", "get_info"]
)

print(f"New key created: {new_key}")
```

### Using curl:

```bash
# Create a key via the API
curl -X POST http://your-api-url.com/api/keys \
  -H "X-API-Key: YOUR_ADMIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "telegram_bot_key",
    "permissions": ["get_video", "get_info"]
  }'
```

## Running the Bot

```bash
python bot.py
```

## Bot Features

- ✅ Create GIFs from YouTube videos.
- ✅ Select a custom time range for the GIF.
- ✅ Displays video info (title, duration, thumbnail).
- ✅ (Optional) Force users to subscribe to a channel.
- ✅ Limit the maximum duration of GIFs.
- ✅ Frame-accurate video trimming.
- ✅ Multilingual support (EN/RU).

## Subscription Channel Setup

1.  Add your bot as an administrator to your channel.
2.  Get the channel ID:
    *   For public channels: use the format `@channel_username`.
    *   For private channels: use a bot like `@getidsbot` to get the numeric ID.
3.  Set the `REQUIRED_CHANNEL_ID` in `config.py`.

## Adding Advertisements

To show an advertisement before the GIF is created:
1.  Customize the `ADVERTISEMENT_MESSAGE` in `config.py`.
2.  In `bot.py`, find the `handle_callback` function and uncomment the lines under the `# if config.ADVERTISEMENT_MESSAGE:` comment.

## Security

⚠️ **Important**:
-   Never share your admin API key.
-   Use a separate key with limited permissions (`get_video`, `get_info`) for the bot.
-   For production environments, store your tokens and keys in environment variables instead of the config file.
