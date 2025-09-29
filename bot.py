import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp_host_api
import config
import os
import tempfile
import requests
from io import BytesIO
from locales import TRANSLATIONS
import time
from urllib.parse import urlparse
import logging
import subprocess

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)


bot = telebot.TeleBot(config.TELEGRAM_BOT_TOKEN)
api = yt_dlp_host_api.api(config.YT_DLP_HOST_URL)
client = api.get_client(config.YT_DLP_API_KEY)
lang = TRANSLATIONS[config.BOT_LANGUAGE]
user_states = {}

FPS_OPTIONS = [10, 15, 20, 25]
WIDTH_OPTIONS = [360, 480, 720, 1080]
COLOR_OPTIONS = [64, 128, 256]

DEFAULT_SETTINGS = {
    'fps': 15,
    'width': 480,
    'colors': 128
}

def is_current(a, b):
    return str(a) == str(b)

def is_youtube_url(url):
    try:
        parsed_url = urlparse(url)
        return (parsed_url.scheme in ['http', 'https'] and
                parsed_url.netloc in {
                    "youtube.com", "www.youtube.com", "m.youtube.com",
                    "youtu.be", "youtube-nocookie.com"
                })
    except Exception:
        return False

def time_to_seconds(time_str):
    try:
        parts = time_str.split(':')
        h, m, s = (0, 0, 0)
        if len(parts) == 3: h, m, s = map(int, parts)
        elif len(parts) == 2: m, s = map(int, parts)
        else: s = int(parts[0])
        return h * 3600 + m * 60 + s
    except:
        return 0

def seconds_to_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def check_subscription(user_id):
    if not config.REQUIRED_CHANNEL_ID: return True
    try:
        member = bot.get_chat_member(config.REQUIRED_CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logging.warning(f"Could not check subscription for {user_id}: {e}")
        return False

def create_time_keyboard(start_time, end_time):
    keyboard = InlineKeyboardMarkup(row_width=2)
    duration_seconds = time_to_seconds(end_time) - time_to_seconds(start_time)
    
    start_btn = InlineKeyboardButton(lang["button_start"].format(time=start_time), callback_data=f"start_{start_time}")
    end_btn = InlineKeyboardButton(lang["button_end"].format(time=end_time), callback_data=f"end_{end_time}")
    duration_btn = InlineKeyboardButton(lang["button_duration"].format(seconds=duration_seconds), callback_data=f"duration_{duration_seconds}")
    settings_btn = InlineKeyboardButton(lang["button_settings"], callback_data="open_settings_main")
    done_btn = InlineKeyboardButton(lang["button_done"], callback_data="done")
    cancel_btn = InlineKeyboardButton(lang["button_cancel"], callback_data="cancel")
    
    keyboard.add(start_btn, end_btn, duration_btn, settings_btn, done_btn, cancel_btn)
    return keyboard

def create_main_settings_keyboard(user_id):
    settings = user_states[user_id]['gif_settings']
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    fps_btn = InlineKeyboardButton(lang["setting_fps"].format(value=settings['fps']), callback_data="open_settings_fps")
    width_btn = InlineKeyboardButton(lang["setting_width"].format(value=settings['width']), callback_data="open_settings_width")
    colors_btn = InlineKeyboardButton(lang["setting_colors"].format(value=settings['colors']), callback_data="open_settings_colors")
    back_btn = InlineKeyboardButton(lang["button_back"], callback_data="back_to_main")
    
    keyboard.add(fps_btn, width_btn, colors_btn, back_btn)
    return keyboard

def create_specific_setting_keyboard(setting_type, current_value, options):
    keyboard = InlineKeyboardMarkup(row_width=4)
    buttons = []
    for option in options:
        text = f"✅ {option}" if is_current(option, current_value) else str(option)
        buttons.append(InlineKeyboardButton(text, callback_data=f"set_{setting_type}_{option}"))
    
    keyboard.add(*buttons)
    keyboard.row(InlineKeyboardButton(lang["button_back_to_settings"], callback_data="open_settings_main"))
    return keyboard

@bot.message_handler(commands=['start', 'help'])
def handle_start(message):
    if not check_subscription(message.from_user.id):
        if config.REQUIRED_CHANNEL_ID:
            bot.send_message(message.chat.id, lang["subscribe_prompt"].format(channel_id=config.REQUIRED_CHANNEL_ID))
            return
    bot.send_message(message.chat.id, lang["start_welcome"].format(max_duration=config.MAX_GIF_DURATION))

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user = message.from_user
    user_id = user.id
    username = user.username or user.first_name
    
    if not check_subscription(user_id):
        if config.REQUIRED_CHANNEL_ID:
            bot.send_message(message.chat.id, lang["subscribe_prompt"].format(channel_id=config.REQUIRED_CHANNEL_ID))
            return

    if user_id in user_states and user_states[user_id].get('waiting_for'):
        state = user_states[user_id]
        time_type = state.get('waiting_for')
        prompt_message_id = state.get('prompt_message_id')
        
        try:
            confirmation_text = ""
            if time_type == 'start_time':
                time_seconds = time_to_seconds(message.text)
                if time_seconds >= time_to_seconds(state['duration']):
                    bot.send_message(message.chat.id, lang["error_start_too_late"])
                    return
                state['start_time'] = message.text
                confirmation_text = lang["start_time_set"]
            
            elif time_type == 'end_time':
                time_seconds = time_to_seconds(message.text)
                start_seconds = time_to_seconds(state['start_time'])
                if time_seconds > time_to_seconds(state['duration']):
                    bot.send_message(message.chat.id, lang["error_end_too_late"])
                    return
                if time_seconds <= start_seconds:
                    bot.send_message(message.chat.id, lang["error_end_before_start"])
                    return
                if (time_seconds - start_seconds) > config.MAX_GIF_DURATION:
                    bot.send_message(message.chat.id, lang["error_duration_too_long"].format(max_duration=config.MAX_GIF_DURATION))
                    return
                state['end_time'] = message.text
                confirmation_text = lang["end_time_set"]
            
            elif time_type == 'duration':
                try:
                    new_duration = int(message.text)
                    if new_duration <= 0: raise ValueError
                except ValueError:
                    bot.send_message(message.chat.id, lang["error_duration_invalid"])
                    return
                if new_duration > config.MAX_GIF_DURATION:
                    bot.send_message(message.chat.id, lang["error_duration_too_long"].format(max_duration=config.MAX_GIF_DURATION))
                    return
                start_seconds = time_to_seconds(state['start_time'])
                new_end_seconds = start_seconds + new_duration
                if new_end_seconds > time_to_seconds(state['duration']):
                    bot.send_message(message.chat.id, lang["error_duration_too_long_video"])
                    return
                state['end_time'] = seconds_to_time(new_end_seconds)
                confirmation_text = lang["duration_set"]

            state['waiting_for'] = None
            del state['prompt_message_id']
            
            confirmation_msg = bot.send_message(message.chat.id, confirmation_text)
            
            keyboard = create_time_keyboard(state['start_time'], state['end_time'])
            bot.edit_message_reply_markup(message.chat.id, state['message_id'], reply_markup=keyboard)
            
            time.sleep(1)
            try:
                bot.delete_message(message.chat.id, prompt_message_id)
                bot.delete_message(message.chat.id, message.message_id)
                bot.delete_message(message.chat.id, confirmation_msg.message_id)
            except Exception: pass
        except Exception as e:
            logging.error(f"Error processing time input for user {user_id}: {e}")
            bot.send_message(message.chat.id, lang["error_invalid_time_format"])
        return
    
    if not is_youtube_url(message.text):
        bot.send_message(message.chat.id, lang["error_invalid_url"])
        return
    
    logging.info(f"User {user_id} ({username}) sent URL: {message.text}")
    loading_msg = bot.send_message(message.chat.id, lang["getting_info"])
    
    try:
        info = client.get_info(url=message.text)
        video_data = info.get_json(['title', 'duration', 'thumbnail', 'width'])
        
        title = video_data.get('title', lang["video_title_default"])
        duration = video_data.get('duration', 0)
        thumbnail = video_data.get('thumbnail', '')
        video_width = video_data.get('width', 0)
        duration_str = seconds_to_time(duration)
        
        start_time = "00:00:00"
        end_time = seconds_to_time(min(16, duration))
        
        caption = lang["video_caption"].format(title=title, duration=duration_str)
        keyboard = create_time_keyboard(start_time, end_time)
        
        msg = None
        if thumbnail:
            try:
                response = requests.get(thumbnail, timeout=10)
                photo = BytesIO(response.content)
                msg = bot.send_photo(message.chat.id, photo, caption=caption, parse_mode='Markdown', reply_markup=keyboard)
            except Exception: pass
        
        if not msg:
            msg = bot.send_message(message.chat.id, caption, parse_mode='Markdown', reply_markup=keyboard)
        
        user_states[user_id] = {
            'url': message.text, 'title': title, 'duration': duration_str,
            'start_time': start_time, 'end_time': end_time, 'message_id': msg.message_id,
            'gif_settings': DEFAULT_SETTINGS.copy(),
            'video_width': video_width
        }
    except Exception as e:
        logging.error(f"Failed to get video info for URL {message.text} by user {user_id}. Error: {e}")
        bot.send_message(message.chat.id, lang["error_getting_info"])
    finally:
        bot.delete_message(message.chat.id, loading_msg.message_id)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    if user_id not in user_states:
        bot.answer_callback_query(call.id, lang["alert_session_expired"], show_alert=True)
        return
    
    state = user_states[user_id]
    data = call.data
    
    if data == "open_settings_main":
        keyboard = create_main_settings_keyboard(user_id)
        bot.edit_message_caption(caption=lang["settings_title"], chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=keyboard)
    
    elif data == "open_settings_fps":
        keyboard = create_specific_setting_keyboard('fps', state['gif_settings']['fps'], FPS_OPTIONS)
        bot.edit_message_caption(caption=lang["settings_menu_title_fps"], chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=keyboard)
    
    elif data == "open_settings_width":
        keyboard = create_specific_setting_keyboard('width', state['gif_settings']['width'], WIDTH_OPTIONS)
        bot.edit_message_caption(caption=lang["settings_menu_title_width"], chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=keyboard)
    
    elif data == "open_settings_colors":
        keyboard = create_specific_setting_keyboard('colors', state['gif_settings']['colors'], COLOR_OPTIONS)
        bot.edit_message_caption(caption=lang["settings_menu_title_colors"], chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=keyboard)
    
    elif data.startswith("set_"):
        _, setting_type, value = data.split('_')
        state['gif_settings'][setting_type] = int(value)
        keyboard = create_main_settings_keyboard(user_id)
        bot.edit_message_caption(caption=lang["settings_title"], chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=keyboard)
        bot.answer_callback_query(call.id, lang["setting_changed"])

    elif data == "back_to_main":
        caption = lang["video_caption"].format(title=state['title'], duration=state['duration'])
        keyboard = create_time_keyboard(state['start_time'], state['end_time'])
        bot.edit_message_caption(caption=caption, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=keyboard, parse_mode='Markdown')
    
    elif data.startswith("start_"):
        state['waiting_for'] = 'start_time'
        prompt_msg = bot.send_message(call.message.chat.id, lang["prompt_start_time"])
        state['prompt_message_id'] = prompt_msg.message_id
        
    elif data.startswith("end_"):
        state['waiting_for'] = 'end_time'
        prompt_msg = bot.send_message(call.message.chat.id, lang["prompt_end_time"])
        state['prompt_message_id'] = prompt_msg.message_id
        
    elif data.startswith("duration_"):
        state['waiting_for'] = 'duration'
        prompt_msg = bot.send_message(call.message.chat.id, lang["prompt_duration"].format(max_duration=config.MAX_GIF_DURATION))
        state['prompt_message_id'] = prompt_msg.message_id

    elif data == "cancel":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        del user_states[user_id]
    
    elif data == "done":
        bot.answer_callback_query(call.id)
        start_seconds = time_to_seconds(state['start_time'])
        end_seconds = time_to_seconds(state['end_time'])
        if end_seconds <= start_seconds:
            bot.answer_callback_query(call.id, lang["alert_end_before_start"], show_alert=True)
            return
        if (end_seconds - start_seconds) > config.MAX_GIF_DURATION:
            bot.answer_callback_query(call.id, lang["alert_duration_too_long"].format(max_duration=config.MAX_GIF_DURATION), show_alert=True)
            return
        
        try: bot.delete_message(call.message.chat.id, state['message_id'])
        except Exception: pass
        
        process_msg = bot.send_message(call.message.chat.id, lang["creating_gif"].format(start_time=state['start_time'], end_time=state['end_time']))
        
        mp4_file, raw_gif_file, final_gif_file = None, None, None
        try:
            mp4_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
            result = client.get_video(
                url=state['url'], output_format='mp4',
                start_time=state['start_time'], end_time=state['end_time'],
                force_keyframes=True)
            result.save_file(mp4_file.name)
            mp4_file.close()

            raw_gif_file = tempfile.NamedTemporaryFile(suffix='.gif', delete=False)
            raw_gif_file.close()
            final_gif_file = tempfile.NamedTemporaryFile(suffix='.gif', delete=False)
            final_gif_file.close()

            settings = state['gif_settings']
            gif_fps = settings['fps']
            gif_width = min(settings['width'], state.get('video_width', settings['width']))
            gif_colors = settings['colors']
            logging.info(f"User {user_id}: Using settings FPS:{gif_fps}, Width:{gif_width}, Colors:{gif_colors}")
            
            ffmpeg_filter = (
                f'fps={gif_fps},scale={gif_width}:-1:flags=lanczos,'
                f'split[s0][s1];[s0]palettegen=stats_mode=diff:max_colors={gif_colors}[p];'
                f'[s1][p]paletteuse=dither=bayer:diff_mode=rectangle'
            )
            
            subprocess.run([
                'ffmpeg', '-i', mp4_file.name, '-vf', ffmpeg_filter,
                '-y', raw_gif_file.name
            ], check=True, capture_output=True, text=True)
            
            logging.info(f"User {user_id}: Optimizing GIF with gifsicle (lossy)...")
            subprocess.run([
                'gifsicle', '-O3', '--lossy=80', raw_gif_file.name, '-o', final_gif_file.name
            ], check=True, capture_output=True, text=True)

            with open(final_gif_file.name, 'rb') as f:
                bot.send_animation(call.message.chat.id, f, caption=lang["gif_ready"].format(title=state['title']))
            
            bot.delete_message(call.message.chat.id, process_msg.message_id)
            del user_states[user_id]
            
        except subprocess.CalledProcessError as e:
            logging.error(f"Processing failed for user {user_id}. Error: {e.stderr}")
            bot.delete_message(call.message.chat.id, process_msg.message_id)
            bot.send_message(call.message.chat.id, lang["error_creating_gif"])
            if user_id in user_states: del user_states[user_id]
        except Exception as e:
            logging.error(f"Failed to create GIF for user {user_id}. URL: {state['url']}. Error: {e}")
            bot.delete_message(call.message.chat.id, process_msg.message_id)
            bot.send_message(call.message.chat.id, lang["error_creating_gif"])
            if user_id in user_states: del user_states[user_id]
        finally:
            if mp4_file and os.path.exists(mp4_file.name): os.unlink(mp4_file.name)
            if raw_gif_file and os.path.exists(raw_gif_file.name): os.unlink(raw_gif_file.name)
            if final_gif_file and os.path.exists(final_gif_file.name): os.unlink(final_gif_file.name)

    if not data.startswith(('start_', 'end_', 'duration_', 'set_')) and data != 'done':
        bot.answer_callback_query(call.id)

if __name__ == '__main__':
    logging.info("Bot is starting...")
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            logging.error(f"Infinity polling exception: {e}")
            logging.info("Restarting in 15 seconds...")
            time.sleep(15)
