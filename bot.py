import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp_host_api
import config
import re
import os
import tempfile
import requests
from io import BytesIO
from locales import TRANSLATIONS
import time

bot = telebot.TeleBot(config.TELEGRAM_BOT_TOKEN)
api = yt_dlp_host_api.api(config.YT_DLP_HOST_URL)
client = api.get_client(config.YT_DLP_API_KEY)
lang = TRANSLATIONS[config.BOT_LANGUAGE]
user_states = {}

def is_youtube_url(url):
    youtube_regex = r'(https?://)?(www\.)?(youtube\.com|youtu\.be|youtube-nocookie\.com)/.+'
    return re.match(youtube_regex, url) is not None

def time_to_seconds(time_str):
    try:
        parts = time_str.split(':')
        if len(parts) == 3:
            h, m, s = map(int, parts)
            return h * 3600 + m * 60 + s
        elif len(parts) == 2:
            m, s = map(int, parts)
            return m * 60 + s
        else:
            return int(parts[0])
    except:
        return 0

def seconds_to_time(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def check_subscription(user_id):
    if not config.REQUIRED_CHANNEL_ID:
        return True
    try:
        member = bot.get_chat_member(config.REQUIRED_CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

def create_time_keyboard(start_time, end_time):
    keyboard = InlineKeyboardMarkup()
    start_btn = InlineKeyboardButton(lang["button_start"].format(time=start_time), callback_data=f"start_{start_time}")
    end_btn = InlineKeyboardButton(lang["button_end"].format(time=end_time), callback_data=f"end_{end_time}")
    done_btn = InlineKeyboardButton(lang["button_done"], callback_data="done")
    cancel_btn = InlineKeyboardButton(lang["button_cancel"], callback_data="cancel")
    keyboard.row(start_btn)
    keyboard.row(end_btn)
    keyboard.row(done_btn, cancel_btn)
    return keyboard

@bot.message_handler(commands=['start', 'help'])
def handle_start(message):
    if not check_subscription(message.from_user.id):
        if config.REQUIRED_CHANNEL_ID:
            bot.send_message(
                message.chat.id,
                lang["subscribe_prompt"].format(channel_id=config.REQUIRED_CHANNEL_ID)
            )
            return
    
    bot.send_message(
        message.chat.id,
        lang["start_welcome"].format(max_duration=config.MAX_GIF_DURATION)
    )

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    
    if not check_subscription(user_id):
        if config.REQUIRED_CHANNEL_ID:
            bot.send_message(
                message.chat.id,
                lang["subscribe_prompt"].format(channel_id=config.REQUIRED_CHANNEL_ID)
            )
            return
    
    if user_id in user_states and user_states[user_id].get('waiting_for'):
        state = user_states[user_id]
        time_type = state.get('waiting_for')
        prompt_message_id = state.get('prompt_message_id')
        
        try:
            time_to_seconds(message.text) # Just to validate format
            
            if time_type == 'start_time':
                time_seconds = time_to_seconds(message.text)
                max_duration_seconds = time_to_seconds(state['duration'])
                if time_seconds >= max_duration_seconds:
                    bot.send_message(message.chat.id, lang["error_start_too_late"])
                    return
                state['start_time'] = message.text
                confirmation_text = lang["start_time_set"]
            
            elif time_type == 'end_time':
                time_seconds = time_to_seconds(message.text)
                max_duration_seconds = time_to_seconds(state['duration'])
                start_seconds = time_to_seconds(state['start_time'])
                if time_seconds > max_duration_seconds:
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
            
            state['waiting_for'] = None
            del state['prompt_message_id']
            
            confirmation_msg = bot.send_message(message.chat.id, confirmation_text)
            
            keyboard = create_time_keyboard(state['start_time'], state['end_time'])
            bot.edit_message_reply_markup(message.chat.id, state['message_id'], reply_markup=keyboard)
            
            time.sleep(0.5)
            try:
                bot.delete_message(message.chat.id, prompt_message_id)
                bot.delete_message(message.chat.id, message.message_id)
                bot.delete_message(message.chat.id, confirmation_msg.message_id)
            except Exception:
                pass

        except Exception:
            bot.send_message(message.chat.id, lang["error_invalid_time_format"])
        return
    
    if not is_youtube_url(message.text):
        bot.send_message(message.chat.id, lang["error_invalid_url"])
        return
    
    loading_msg = bot.send_message(message.chat.id, lang["getting_info"])
    
    try:
        info = client.get_info(url=message.text)
        video_data = info.get_json(['title', 'duration', 'thumbnail'])
        
        title = video_data.get('title', lang["video_title_default"])
        duration = video_data.get('duration', 0)
        thumbnail = video_data.get('thumbnail', '')
        duration_str = seconds_to_time(duration)
        
        start_time = "00:00:00"
        end_time = seconds_to_time(min(16, duration))
        
        caption = lang["video_caption"].format(title=title, duration=duration_str)
        keyboard = create_time_keyboard(start_time, end_time)
        
        msg = None
        if thumbnail:
            try:
                response = requests.get(thumbnail)
                photo = BytesIO(response.content)
                msg = bot.send_photo(message.chat.id, photo, caption=caption, parse_mode='Markdown', reply_markup=keyboard)
            except Exception:
                pass
        
        if not msg:
            msg = bot.send_message(message.chat.id, caption, parse_mode='Markdown', reply_markup=keyboard)
        
        user_states[user_id] = {
            'url': message.text, 'title': title, 'duration': duration_str,
            'start_time': start_time, 'end_time': end_time, 'message_id': msg.message_id
        }
        
    except Exception:
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
    
    if call.data.startswith("start_"):
        bot.answer_callback_query(call.id)
        state['waiting_for'] = 'start_time'
        prompt_msg = bot.send_message(call.message.chat.id, lang["prompt_start_time"])
        state['prompt_message_id'] = prompt_msg.message_id
        
    elif call.data.startswith("end_"):
        bot.answer_callback_query(call.id)
        state['waiting_for'] = 'end_time'
        prompt_msg = bot.send_message(call.message.chat.id, lang["prompt_end_time"])
        state['prompt_message_id'] = prompt_msg.message_id
        
    elif call.data == "cancel":
        bot.answer_callback_query(call.id, lang["alert_cancelled"])
        del user_states[user_id]
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
        
    elif call.data == "done":
        bot.answer_callback_query(call.id)
        
        start_seconds = time_to_seconds(state['start_time'])
        end_seconds = time_to_seconds(state['end_time'])
        
        if end_seconds <= start_seconds:
            bot.answer_callback_query(call.id, lang["alert_end_before_start"], show_alert=True)
            return
        
        if (end_seconds - start_seconds) > config.MAX_GIF_DURATION:
            bot.answer_callback_query(
                call.id,
                lang["alert_duration_too_long"].format(max_duration=config.MAX_GIF_DURATION),
                show_alert=True
            )
            return
        
        # <<<--- ВОТ ИЗМЕНЕНИЕ ---<<<
        # Удаляем сообщение с превью и кнопками вместо редактирования
        try:
            bot.delete_message(call.message.chat.id, state['message_id'])
        except Exception:
            pass # Если не получилось удалить, не страшно, продолжаем
        
        process_msg = bot.send_message(
            call.message.chat.id,
            lang["creating_gif"].format(start_time=state['start_time'], end_time=state['end_time'])
        )
        
        tmp_file = None
        try:
            tmp_file = tempfile.NamedTemporaryFile(suffix='.gif', delete=False)
            tmp_filename = tmp_file.name
            tmp_file.close()

            result = client.get_video(
                url=state['url'], output_format='gif',
                start_time=state['start_time'], end_time=state['end_time'],
                force_keyframes=True
            )
            result.save_file(tmp_filename)
            
            with open(tmp_filename, 'rb') as gif_file:
                bot.send_animation(
                    call.message.chat.id,
                    gif_file,
                    caption=lang["gif_ready"].format(title=state['title'])
                )
            
            bot.delete_message(call.message.chat.id, process_msg.message_id)
            del user_states[user_id]
            
        except Exception:
            bot.delete_message(call.message.chat.id, process_msg.message_id)
            bot.send_message(call.message.chat.id, lang["error_creating_gif"])
            if user_id in user_states:
                del user_states[user_id]
        finally:
            if tmp_file and os.path.exists(tmp_file.name):
                os.unlink(tmp_file.name)

if __name__ == '__main__':
    print("🤖 Bot is running...")
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"Error: {e}")
            print("Restarting in 15 seconds...")
            time.sleep(15)
