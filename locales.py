TRANSLATIONS = {
    "en": {
        "subscribe_prompt": "❌ To use the bot, you need to subscribe to the channel:\n"
                            "👉 {channel_id}\n\n"
                            "After subscribing, press /start",
        "start_welcome": "🎬 Hi! I'll help you create a GIF from a YouTube video.\n\n"
                         "📋 How to use:\n"
                         "1. Send me a link to a YouTube video\n"
                         "2. I'll show you information about the video\n"
                         "3. Choose the start and end times for the GIF\n"
                         "4. Maximum duration: {max_duration} seconds\n\n"
                         "🔗 Just send the video link!",
        "prompt_start_time": "⏰ Enter the start time in HH:MM:SS format (e.g., 00:00:05):",
        "prompt_end_time": "⏰ Enter the end time in HH:MM:SS format (e.g., 00:00:16):",
        "prompt_duration": "⏱️ Enter the desired duration in seconds (max: {max_duration}):",
        "start_time_set": "✅ Start time set!",
        "end_time_set": "✅ End time set!",
        "duration_set": "✅ Duration set!",
        "getting_info": "⏳ Getting video info...",
        "video_caption": "📹 **{title}**\n"
                         "⏱ Duration: {duration}\n\n"
                         "Select the time range for the GIF:",
        "video_title_default": "Untitled",
        "creating_gif": "🎬 Creating GIF...\n"
                        "📍 Start: {start_time}\n"
                        "🏁 End: {end_time}\n\n"
                        "⏳ This may take some time...",
        "gif_ready": "✅ GIF is ready!\n📹 {title}",
        "button_start": "📍 Start: {time}",
        "button_end": "🏁 End: {time}",
        "button_duration": "⏱️ Duration: {seconds}s",
        "button_done": "✅ Done",
        "button_cancel": "❌ Cancel",
        "error_invalid_url": "❌ Please send a valid YouTube video link",
        "error_getting_info": "❌ Error getting video information.",
        "error_invalid_time_format": "❌ Invalid time format. Use HH:MM:SS",
        "error_duration_invalid": "❌ Invalid duration. Please enter a number.",
        "error_start_too_late": "❌ Start time cannot be greater than video duration",
        "error_end_too_late": "❌ End time cannot be greater than video duration",
        "error_end_before_start": "❌ End time must be after the start time",
        "error_duration_too_long": "❌ Maximum GIF duration: {max_duration} seconds",
        "error_duration_too_long_video": "❌ The resulting duration extends beyond the end of the video.",
        "error_creating_gif": "❌ An error occurred while creating the GIF.",
        "alert_session_expired": "❌ Session expired. Please send the link again.",
        "alert_cancelled": "❌ Cancelled",
        "alert_end_before_start": "❌ End time must be after the start time!",
        "alert_duration_too_long": "❌ Maximum duration: {max_duration} seconds!",
    },
    "ru": {
        "subscribe_prompt": "❌ Для использования бота необходимо подписаться на канал:\n"
                            "👉 {channel_id}\n\n"
                            "После подписки нажмите /start",
        "start_welcome": "🎬 Привет! Я помогу тебе создать GIF из YouTube видео.\n\n"
                         "📋 Как использовать:\n"
                         "1. Отправь мне ссылку на YouTube видео\n"
                         "2. Я покажу информацию о видео\n"
                         "3. Выбери начало и конец для GIF\n"
                         "4. Максимальная длительность: {max_duration} секунд\n\n"
                         "🔗 Просто отправь ссылку на видео!",
        "prompt_start_time": "⏰ Введите время начала в формате HH:MM:SS (например: 00:00:05):",
        "prompt_end_time": "⏰ Введите время конца в формате HH:MM:SS (например: 00:00:16):",
        "prompt_duration": "⏱️ Введите желаемую длительность в секундах (макс: {max_duration}):",
        "start_time_set": "✅ Начало установлено!",
        "end_time_set": "✅ Конец установлен!",
        "duration_set": "✅ Длительность установлена!",
        "getting_info": "⏳ Получаю информацию о видео...",
        "video_caption": "📹 **{title}**\n"
                         "⏱ Длительность: {duration}\n\n"
                         "Выберите временной отрезок для GIF:",
        "video_title_default": "Без названия",
        "creating_gif": "🎬 Создаю GIF...\n"
                        "📍 Начало: {start_time}\n"
                        "🏁 Конец: {end_time}\n\n"
                        "⏳ Это может занять некоторое время...",
        "gif_ready": "✅ GIF готов!\n📹 {title}",
        "button_start": "📍 Начало: {time}",
        "button_end": "🏁 Конец: {time}",
        "button_duration": "⏱️ Длительность: {seconds} сек",
        "button_done": "✅ Готово",
        "button_cancel": "❌ Отмена",
        "error_invalid_url": "❌ Пожалуйста, отправьте корректную ссылку на YouTube видео",
        "error_getting_info": "❌ Ошибка при получении информации о видео.",
        "error_invalid_time_format": "❌ Неверный формат времени. Используйте HH:MM:SS",
        "error_duration_invalid": "❌ Неверный формат длительности. Введите число.",
        "error_start_too_late": "❌ Начало не может быть больше длительности видео",
        "error_end_too_late": "❌ Конец не может быть больше длительности видео",
        "error_end_before_start": "❌ Конец должен быть после начала",
        "error_duration_too_long": "❌ Максимальная длительность GIF: {max_duration} секунд",
        "error_duration_too_long_video": "❌ Указанная длительность выходит за пределы видео.",
        "error_creating_gif": "❌ Ошибка при создании GIF.",
        "alert_session_expired": "❌ Сессия истекла. Отправьте ссылку заново.",
        "alert_cancelled": "❌ Отменено",
        "alert_end_before_start": "❌ Конец должен быть после начала!",
        "alert_duration_too_long": "❌ Максимальная длительность: {max_duration} секунд!",
    }
}
