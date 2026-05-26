import os
import logging
import random
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, JobQueue
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# Marriage advice categories
MARRIAGE_ADVICE = {
    'communication': [
        "💬 **Communication Tip:** Listen to understand, not to respond. Sometimes your spouse just needs to be heard.",
        "🗣️ Use 'I feel' statements instead of 'You always' to avoid sounding accusatory.",
        "📞 Set aside 15 minutes daily to talk without phones or TV distractions.",
        "🤝 When arguing, focus on the issue, not attacking your partner's character."
    ],
    'romance': [
        "❤️ **Keep the Spark Alive:** Surprise your spouse with a love note in their lunchbox.",
        "🌹 Plan a date night at least twice a month - even if it's just watching a movie at home.",
        "💑 Hold hands while watching TV or walking together. Small touches matter!",
        "🎵 Create 'your song' and dance to it in the kitchen while cooking."
    ],
    'conflict': [
        "⚡ **Handling Disagreements:** Never go to bed angry. Take a 20-minute break to cool down, then talk.",
        "🤲 Apologize even if you're not wrong - sometimes peace is more important than being right.",
        "⏸️ Use a 'safe word' to pause heated arguments before they escalate.",
        "🔄 Remember: It's you and your spouse vs the problem, not vs each other."
    ],
    'growth': [
        "🌱 **Growing Together:** Set shared goals and work towards them as a team.",
        "📚 Read relationship books together or listen to marriage podcasts.",
        "🎯 Celebrate each other's wins, no matter how small.",
        "💪 Support each other's individual hobbies and personal growth."
    ],
    'daily_tips': [
        "☀️ **Morning Ritual:** Start each day with a kiss and 'I love you' before checking phones.",
        "🍳 Do small acts of kindness - make coffee, pack lunch, leave a sweet note.",
        "📝 Keep a gratitude journal together, write 3 things you appreciate about each other weekly.",
        "😊 Smile at your spouse first thing in the morning and last thing at night."
    ]
}

# News categories with APIs (using free APIs)
NEWS_SOURCES = {
    'general': 'https://min-api.cryptocompare.com/data/v2/news/?lang=EN',
    'technology': 'https://min-api.cryptocompare.com/data/v2/news/?lang=EN&categories=Tech',
    'world': 'https://min-api.cryptocompare.com/data/v2/news/?lang=EN&categories=World'
}

# Store user preferences
user_preferences = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("📰 Get News", callback_data='news_menu')],
        [InlineKeyboardButton("💑 Marriage Advice", callback_data='advice_menu')],
        [InlineKeyboardButton("📊 Daily Combo", callback_data='daily_combo')],
        [InlineKeyboardButton("🔔 Subscribe (Daily Updates)", callback_data='subscribe')],
        [InlineKeyboardButton("ℹ️ About", callback_data='about')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"📰💑 **Welcome to News & Marriage Advice Bot, {user.first_name}!**\n\n"
        f"Your one-stop destination for:\n"
        f"• 📰 Latest news updates\n"
        f"• 💑 Expert marriage advice\n"
        f"• 🌟 Daily relationship tips\n\n"
        f"Choose an option below:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def news_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🌍 General News", callback_data='news_general')],
        [InlineKeyboardButton("💻 Technology", callback_data='news_technology')],
        [InlineKeyboardButton("🌐 World News", callback_data='news_world')],
        [InlineKeyboardButton("🔙 Back to Main", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "**📰 Select News Category:**",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def get_news(category='general'):
    """Fetch news from API"""
    try:
        # Using free CryptoCompare news API (no API key needed for basic usage)
        url = NEWS_SOURCES.get(category, NEWS_SOURCES['general'])
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'Data' in data and len(data['Data']) > 0:
                articles = data['Data'][:5]  # Get top 5 news
                news_list = []
                for article in articles:
                    title = article.get('title', 'No title')
                    source = article.get('source_info', {}).get('name', 'Unknown')
                    url_link = article.get('url', '#')
                    news_list.append(f"📰 **{title}**\n📌 *Source: {source}*\n🔗 [Read more]({url_link})")
                return news_list
        return None
    except Exception as e:
        logging.error(f"News fetch error: {e}")
        return None

async def send_news(update: Update, context: ContextTypes.DEFAULT_TYPE, category='general'):
    query = update.callback_query
    await query.edit_message_text("📡 Fetching latest news... Please wait ⏳")
    
    news_list = await get_news(category)
    
    if news_list:
        keyboard = [[InlineKeyboardButton("🔄 Refresh News", callback_data=f'news_{category}')],
                    [InlineKeyboardButton("🔙 News Menu", callback_data='news_menu')],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data='main_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = f"**📰 {category.upper()} NEWS**\n\n" + "\n\n---\n\n".join(news_list)
        await query.edit_message_text(
            message[:4000],  # Telegram limit
            parse_mode='Markdown',
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
    else:
        await query.edit_message_text(
            "⚠️ Unable to fetch news right now. Please try again later.\n\n"
            "Here's a marriage tip instead:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("💑 Get Marriage Tip", callback_data='random_advice'),
                InlineKeyboardButton("🔙 Back", callback_data='main_menu')
            ]])
        )

async def advice_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("💬 Communication", callback_data='advice_communication')],
        [InlineKeyboardButton("❤️ Romance & Date Ideas", callback_data='advice_romance')],
        [InlineKeyboardButton("⚡ Conflict Resolution", callback_data='advice_conflict')],
        [InlineKeyboardButton("🌱 Growing Together", callback_data='advice_growth')],
        [InlineKeyboardButton("☀️ Daily Tips", callback_data='advice_daily_tips')],
        [InlineKeyboardButton("🎲 Random Advice", callback_data='random_advice')],
        [InlineKeyboardButton("🔙 Back to Main", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "**💑 Marriage Advice Categories:**\n\n"
        "Choose a topic to get expert advice:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def send_advice(update: Update, context: ContextTypes.DEFAULT_TYPE, category=None):
    query = update.callback_query
    
    if category and category in MARRIAGE_ADVICE:
        advice_list = MARRIAGE_ADVICE[category]
    else:
        # Random advice from all categories
        all_advice = []
        for advices in MARRIAGE_ADVICE.values():
            all_advice.extend(advices)
        advice_list = all_advice
    
    advice = random.choice(advice_list)
    
    keyboard = [
        [InlineKeyboardButton("🔄 More Advice", callback_data=f'advice_{category}' if category else 'random_advice')],
        [InlineKeyboardButton("📋 Advice Menu", callback_data='advice_menu')],
        [InlineKeyboardButton("🏠 Main Menu", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    category_name = category.replace('_', ' ').title() if category else "Random"
    await query.edit_message_text(
        f"**💑 {category_name} Advice:**\n\n{advice}\n\n",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def daily_combo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send news + marriage advice together"""
    query = update.callback_query
    await query.edit_message_text("📡 Preparing your daily combo... ⏳")
    
    # Get news
    news_list = await get_news('general')
    
    # Get random marriage advice
    all_advice = []
    for advices in MARRIAGE_ADVICE.values():
        all_advice.extend(advices)
    advice = random.choice(all_advice)
    
    if news_list:
        top_news = news_list[0]
        message = f"**🌟 YOUR DAILY COMBO 🌟**\n\n"
        message += f"**📰 TOP NEWS:**\n{top_news}\n\n"
        message += f"**💑 MARRIAGE ADVICE:**\n{advice}\n\n"
        message += f"💡 Tip: Use the menu for more news and advice!"
    else:
        message = f"**🌟 DAILY MARRIAGE ADVICE 🌟**\n\n{advice}\n\n"
        message += f"⚠️ News unavailable at the moment. Try again later!"
    
    keyboard = [[InlineKeyboardButton("🔄 Refresh Combo", callback_data='daily_combo')],
                [InlineKeyboardButton("🏠 Main Menu", callback_data='main_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    if user_id not in user_preferences:
        user_preferences[user_id] = {'subscribed': True}
        await query.edit_message_text(
            "✅ **Subscribed Successfully!**\n\n"
            "You'll receive daily updates with:\n"
            "• 📰 Top news of the day\n"
            "• 💑 Marriage advice\n\n"
            "Use /unsubscribe to stop daily updates.",
            parse_mode='Markdown'
        )
    else:
        await query.edit_message_text(
            "ℹ️ You're already subscribed!\n"
            "Use /unsubscribe to stop daily updates.",
            parse_mode='Markdown'
        )

async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_preferences:
        del user_preferences[user_id]
        await update.message.reply_text(
            "❌ Unsubscribed successfully!\n"
            "You won't receive daily updates anymore.\n"
            "Use /start to subscribe again."
        )
    else:
        await update.message.reply_text("You weren't subscribed!")

async def daily_digest(context: ContextTypes.DEFAULT_TYPE):
    """Send daily digest to all subscribers"""
    news_list = await get_news('general')
    all_advice = []
    for advices in MARRIAGE_ADVICE.values():
        all_advice.extend(advices)
    advice = random.choice(all_advice)
    
    if news_list:
        top_news = news_list[0]
        message = f"**📆 DAILY DIGEST - {datetime.now().strftime('%B %d, %Y')}**\n\n"
        message += f"**📰 NEWS:**\n{top_news}\n\n"
        message += f"**💑 RELATIONSHIP WISDOM:**\n{advice}\n\n"
        message += f"💡 Interact with the bot for more: /start"
    else:
        message = f"**📆 DAILY MARRIAGE ADVICE**\n\n{advice}\n\n/start for more!"
    
    # Send to all subscribers
    for user_id in user_preferences:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
        except Exception as e:
            logging.error(f"Failed to send to {user_id}: {e}")

async def random_advice_only(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send random advice without callback"""
    all_advice = []
    for advices in MARRIAGE_ADVICE.values():
        all_advice.extend(advices)
    advice = random.choice(all_advice)
    
    await update.message.reply_text(
        f"💑 **Random Marriage Advice:**\n\n{advice}\n\n"
        f"Want more? Use /start for categories!",
        parse_mode='Markdown'
    )

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "**📰💑 About This Bot**\n\n"
        "**Features:**\n"
        "• Latest news from around the world\n"
        "• Expert marriage and relationship advice\n"
        "• Daily tips for a stronger marriage\n"
        "• Customizable categories\n"
        "• Daily digest subscription\n\n"
        "**Commands:**\n"
        "/start - Open main menu\n"
        "/advice - Get random marriage advice\n"
        "/unsubscribe - Stop daily updates\n"
        "/help - Show this help\n\n"
        "**Version:** 1.0\n"
        "Built with ❤️ for better relationships and informed living!",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🏠 Main Menu", callback_data='main_menu')
        ]])
    )

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await start(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "**Available Commands:**\n\n"
        "/start - Launch the bot\n"
        "/advice - Get random marriage advice\n"
        "/unsubscribe - Stop daily updates\n"
        "/help - Show this help\n\n"
        "💡 Use the interactive buttons for best experience!",
        parse_mode='Markdown'
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Error: {context.error}")

def main():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not set!")
        return
    
    app = Application.builder().token(token).build()
    
    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("advice", random_advice_only))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe))
    
    # Add callback handlers
    app.add_handler(CallbackQueryHandler(news_menu, pattern='^news_menu$'))
    app.add_handler(CallbackQueryHandler(advice_menu, pattern='^advice_menu$'))
    app.add_handler(CallbackQueryHandler(daily_combo, pattern='^daily_combo$'))
    app.add_handler(CallbackQueryHandler(subscribe, pattern='^subscribe$'))
    app.add_handler(CallbackQueryHandler(about, pattern='^about$'))
    app.add_handler(CallbackQueryHandler(main_menu, pattern='^main_menu$'))
    app.add_handler(CallbackQueryHandler(send_advice, pattern='^advice_'))
    app.add_handler(CallbackQueryHandler(random_advice_only_callback, pattern='^random_advice$'))
    app.add_handler(CallbackQueryHandler(lambda u,c: send_news(u,c,'general'), pattern='^news_general$'))
    app.add_handler(CallbackQueryHandler(lambda u,c: send_news(u,c,'technology'), pattern='^news_technology$'))
    app.add_handler(CallbackQueryHandler(lambda u,c: send_news(u,c,'world'), pattern='^news_world$'))
    
    app.add_error_handler(error_handler)
    
    # Setup daily job (9 AM every day)
    job_queue = app.job_queue
    if job_queue:
        job_queue.run_daily(daily_digest, time=datetime.strptime("09:00", "%H:%M").time())
        print("⏰ Daily digest scheduled for 9:00 AM")
    
    print("📰💑 News & Marriage Advice Bot is running...")
    app.run_polling()

async def random_advice_only_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    all_advice = []
    for advices in MARRIAGE_ADVICE.values():
        all_advice.extend(advices)
    advice = random.choice(all_advice)
    
    keyboard = [[InlineKeyboardButton("🔄 Another Advice", callback_data='random_advice')],
                [InlineKeyboardButton("📋 Advice Menu", callback_data='advice_menu')],
                [InlineKeyboardButton("🏠 Main Menu", callback_data='main_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"💑 **Random Marriage Advice:**\n\n{advice}\n\n",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

if __name__ == '__main__':
    main()
