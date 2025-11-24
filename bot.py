import os
import json
import random
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
    ConversationHandler
)

# === CONFIGURATION ===
TOKEN = os.environ.get('BOT_TOKEN', '8551305615:AAEdnWWsmqoWTT_pqiCQd-qO__LyVK7HG8E')
ADMIN_ID = int(os.environ.get('ADMIN_ID', '7472543084'))  # PALITAN MO ITO NG ID MO
KEYS_FILE = "keys.json"
DATABASE_FILES = ["v1.txt", "v2.txt", "v3.txt", "v4.txt", "v5.txt"]
USED_ACCOUNTS_FILE = "used_accounts.txt"
BANNED_USERS_FILE = "banned_users.txt"
FEEDBACK_FILE = "feedback.txt"
LINES_TO_SEND = 10

# === STATES FOR CONVERSATION HANDLERS ===
AWAITING_FEEDBACK, AWAITING_BROADCAST, AWAITING_BAN_USER = range(3)

# === DOMAIN LIST ===
DOMAINS = [
    "garena", "roblox", "mobilelegends", "pubg", "codashop", 
    "facebook", "netflix", "tiktok", "freefire"
]

# === EMOJI THEME ===
EMOJIS = {
    "main": "🌟",
    "generate": "🔍",
    "admin": "🛠",
    "info": "ℹ️",
    "help": "🆘",
    "time": "⏳",
    "stats": "📊",
    "feedback": "📝",
    "key": "🔑",
    "back": "🔙",
    "success": "✅",
    "error": "❌",
    "warning": "⚠️",
    "broadcast": "📢",
    "ban": "🚫",
    "users": "👥",
    "domain": "🌐"
}

# === LOAD DATABASE ===
if not os.path.exists(USED_ACCOUNTS_FILE):
    open(USED_ACCOUNTS_FILE, "w").close()

if not os.path.exists(BANNED_USERS_FILE):
    open(BANNED_USERS_FILE, "w").close()

if not os.path.exists(FEEDBACK_FILE):
    open(FEEDBACK_FILE, "w").close()

def load_keys():
    if os.path.exists(KEYS_FILE):
        try:
            with open(KEYS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"keys": {}, "user_keys": {}, "logs": {}}
    return {"keys": {}, "user_keys": {}, "logs": {}}

def save_keys(data):
    with open(KEYS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

keys_data = load_keys()

# === UTILITY FUNCTIONS ===
def generate_random_key(length=8):
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "TOLLIPOP-" + ''.join(random.choices(chars, k=length))

def get_expiry_time(duration):
    now = datetime.now()
    duration_map = {
        "1h": 3600, "1d": 86400, "7d": 604800, "30d": 2592000
    }
    return None if duration == "lifetime" else (now + timedelta(seconds=duration_map[duration])).timestamp()

def is_admin(user_id):
    return str(user_id) == str(ADMIN_ID)

def is_banned(user_id):
    if not os.path.exists(BANNED_USERS_FILE):
        return False
    with open(BANNED_USERS_FILE, "r") as f:
        return str(user_id) in f.read().splitlines()

def format_time(seconds):
    if seconds is None:
        return "Lifetime"
    dt = datetime.fromtimestamp(seconds)
    return dt.strftime('%Y-%m-%d %H:%M:%S')

# === BEAUTIFUL MESSAGE TEMPLATES ===
def create_main_menu():
    keyboard = [
        [InlineKeyboardButton(f"{EMOJIS['generate']} Generate Accounts", callback_data="main_generate")],
        [InlineKeyboardButton(f"{EMOJIS['info']} Bot Info", callback_data="main_info"),
         InlineKeyboardButton(f"{EMOJIS['help']} Help", callback_data="main_help")],
        [InlineKeyboardButton(f"{EMOJIS['feedback']} Feedback", callback_data="main_feedback"),
         InlineKeyboardButton(f"{EMOJIS['key']} Redeem Key", callback_data="main_redeem")]
    ]
    
    if is_admin(ADMIN_ID):
        keyboard.append([InlineKeyboardButton(f"{EMOJIS['admin']} ADMIN PANEL", callback_data="main_admin")])
    
    return InlineKeyboardMarkup(keyboard)

def create_admin_menu():
    keyboard = [
        [InlineKeyboardButton(f"{EMOJIS['key']} Generate Key", callback_data="admin_genkey"),
         InlineKeyboardButton(f"{EMOJIS['stats']} Stats", callback_data="admin_stats")],
        [InlineKeyboardButton(f"{EMOJIS['broadcast']} Broadcast", callback_data="admin_broadcast"),
         InlineKeyboardButton(f"{EMOJIS['ban']} Ban User", callback_data="admin_ban")],
        [InlineKeyboardButton(f"{EMOJIS['back']} Main Menu", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_key_duration_menu():
    keyboard = [
        [InlineKeyboardButton("1 Hour", callback_data="genkey_1h"),
         InlineKeyboardButton("1 Day", callback_data="genkey_1d")],
        [InlineKeyboardButton("7 Days", callback_data="genkey_7d"),
         InlineKeyboardButton("30 Days", callback_data="genkey_30d")],
        [InlineKeyboardButton(f"{EMOJIS['back']} Admin Panel", callback_data="main_admin")]
    ]
    return InlineKeyboardMarkup(keyboard)

# === COMMAND HANDLERS ===
async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if is_banned(user_id):
        return await update.message.reply_text(
            f"{EMOJIS['error']} You have been banned from using this bot."
        )
    
    welcome_message = (
        f"{EMOJIS['main']} *𝗪𝗘𝗟𝗖𝗢𝗠𝗘 𝗧𝗢 𝗧𝗢𝗟𝗟𝗜𝗣𝗢𝗣 𝗙𝗥𝗘𝗘 𝗕𝗢𝗧!* {EMOJIS['main']}\n\n"
        f"{EMOJIS['success']} Generate premium accounts with ease\n"
        f"{EMOJIS['success']} Fast and reliable service\n"
        f"{EMOJIS['success']} Multiple domains available\n\n"
        "Select an option below:"
    )
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=create_main_menu(),
        parse_mode="Markdown"
    )

async def redeem_key(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if is_banned(user_id):
        return await update.message.reply_text(
            f"{EMOJIS['error']} You have been banned from using this bot."
        )
    
    if len(context.args) != 1:
        keyboard = [[InlineKeyboardButton(f"{EMOJIS['back']} Main Menu", callback_data="main_menu")]]
        return await update.message.reply_text(
            f"{EMOJIS['warning']} *Invalid Usage!*\n\n"
            "Usage: `/key <your_key>`\n\n"
            "Example: `/key TOLLIPOP-ABCD1234`",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    chat_id = str(user_id)
    entered_key = context.args[0].upper()

    if entered_key not in keys_data["keys"]:
        return await update.message.reply_text(f"{EMOJIS['error']} Invalid or expired key!")

    expiry = keys_data["keys"][entered_key]
    if expiry is not None and datetime.now().timestamp() > expiry:
        del keys_data["keys"][entered_key]
        save_keys(keys_data)
        return await update.message.reply_text(f"{EMOJIS['error']} This key has already expired!")

    keys_data["user_keys"][chat_id] = expiry
    del keys_data["keys"][entered_key]
    save_keys(keys_data)

    expiry_text = "Lifetime" if expiry is None else format_time(expiry)
    
    keyboard = [[InlineKeyboardButton(f"{EMOJIS['generate']} Generate Accounts", callback_data="main_generate")]]
    
    await update.message.reply_text(
        f"{EMOJIS['success']} *Key Redeemed Successfully!*\n\n"
        f"{EMOJIS['key']} Key: `{entered_key}`\n"
        f"{EMOJIS['time']} Expires: `{expiry_text}`\n\n"
        "You can now generate premium accounts!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# === CALLBACK QUERY HANDLERS ===
async def main_menu_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        f"{EMOJIS['main']} *𝗧𝗢𝗟𝗟𝗜𝗣𝗢𝗣 𝗔𝗖𝗖𝗢𝗨𝗡𝗧 𝗚𝗘𝗡𝗘𝗥𝗔𝗧𝗢𝗥 𝗕𝗢𝗧* {EMOJIS['main']}\n\n"
        "Select an option below:",
        reply_markup=create_main_menu(),
        parse_mode="Markdown"
    )

async def admin_panel(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return await query.edit_message_text(
            f"{EMOJIS['error']} You are not authorized to access this panel!"
        )
    
    await query.edit_message_text(
        f"{EMOJIS['admin']} *ADMIN PANEL* {EMOJIS['admin']}\n\n"
        "Select an option to manage the bot:",
        reply_markup=create_admin_menu(),
        parse_mode="Markdown"
    )

async def generate_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if is_banned(user_id):
        return await query.message.reply_text(
            f"{EMOJIS['error']} You have been banned from using this bot."
        )
    
    chat_id = str(user_id)
    if chat_id not in keys_data["user_keys"]:
        return await query.message.reply_text(
            f"{EMOJIS['error']} You need a valid key to use this feature!"
        )

    keyboard = []
    for i in range(0, len(DOMAINS), 2):
        row = []
        if i < len(DOMAINS):
            row.append(InlineKeyboardButton(DOMAINS[i], callback_data=f"generate_{DOMAINS[i]}"))
        if i+1 < len(DOMAINS):
            row.append(InlineKeyboardButton(DOMAINS[i+1], callback_data=f"generate_{DOMAINS[i+1]}"))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton(f"{EMOJIS['back']} Main Menu", callback_data="main_menu")])
    
    await query.edit_message_text(
        f"{EMOJIS['generate']} *Select a domain to generate:*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def generate_filtered_accounts(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    selected_domain = query.data.replace("generate_", "")

    if is_banned(user_id):
        return await query.message.reply_text(
            f"{EMOJIS['error']} You have been banned from using this bot."
        )
    
    chat_id = str(user_id)
    if chat_id not in keys_data["user_keys"]:
        return await query.message.reply_text(
            f"{EMOJIS['error']} You need a valid key to use this feature!"
        )

    processing_msg = await query.message.reply_text(
        f"{EMOJIS['generate']} *Processing... Please wait.*"
    )

    # Load used accounts
    try:
        with open(USED_ACCOUNTS_FILE, "r", encoding="utf-8", errors="ignore") as f:
            used_accounts = set(f.read().splitlines())
    except:
        used_accounts = set()

    # Find matching lines
    matched_lines = []
    for db_file in DATABASE_FILES:
        if len(matched_lines) >= LINES_TO_SEND:
            break
        try:
            with open(db_file, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    stripped_line = line.strip()
                    if selected_domain.lower() in stripped_line.lower() and stripped_line not in used_accounts:
                        matched_lines.append(stripped_line)
                        if len(matched_lines) >= LINES_TO_SEND:
                            break
        except Exception as e:
            print(f"Error reading {db_file}: {str(e)}")
            continue

    if not matched_lines:
        return await processing_msg.edit_text(
            f"{EMOJIS['error']} *No available accounts found for this domain!*",
            parse_mode="Markdown"
        )

    # Append used accounts
    with open(USED_ACCOUNTS_FILE, "a", encoding="utf-8", errors="ignore") as f:
        f.write("\n".join(matched_lines) + "\n")

    # Send accounts as message instead of file
    accounts_text = f"🔑 *{selected_domain.upper()} ACCOUNTS* 🔑\n\n"
    accounts_text += f"📦 Total Accounts: {len(matched_lines)}\n"
    accounts_text += f"⏳ Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    for i, account in enumerate(matched_lines[:10], 1):
        accounts_text += f"{i}. `{account}`\n"
    
    accounts_text += f"\n{EMOJIS['success']} *Enjoy your accounts!*"

    await processing_msg.delete()
    await query.message.reply_text(
        accounts_text,
        parse_mode="Markdown"
    )

async def generate_key_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return await query.edit_message_text(
            f"{EMOJIS['error']} You are not authorized to use this feature!"
        )
    
    await query.edit_message_text(
        f"{EMOJIS['key']} *Generate New Key* {EMOJIS['key']}\n\n"
        "Select the duration for the new key:",
        reply_markup=create_key_duration_menu(),
        parse_mode="Markdown"
    )

async def generate_key(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return await query.edit_message_text(
            f"{EMOJIS['error']} You are not authorized to use this feature!"
        )
    
    duration = query.data.replace("genkey_", "")
    new_key = generate_random_key()
    expiry = get_expiry_time(duration)

    keys_data["keys"][new_key] = expiry
    save_keys(keys_data)

    await query.edit_message_text(
        f"{EMOJIS['success']} *New Key Generated!*\n\n"
        f"{EMOJIS['key']} Key: `{new_key}`\n"
        f"{EMOJIS['time']} Duration: `{duration}`\n\n"
        "✅ Share this key with your users!",
        parse_mode="Markdown"
    )

async def bot_info(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    total_users = len(keys_data["user_keys"])
    active_users = sum(1 for expiry in keys_data["user_keys"].values() 
                   if expiry is None or datetime.now().timestamp() < expiry)
    
    keyboard = [[InlineKeyboardButton(f"{EMOJIS['back']} Main Menu", callback_data="main_menu")]]
    
    await query.edit_message_text(
        f"{EMOJIS['info']} *𝗧𝗢𝗟𝗟𝗜𝗣𝗢𝗣 𝗔𝗖𝗖𝗢𝗨𝗡𝗧 𝗚𝗘𝗡𝗘𝗥𝗔𝗧𝗢𝗥 𝗕𝗢𝗧*\n\n"
        f"{EMOJIS['success']} *Version:* 2.0 Simple\n"
        f"{EMOJIS['success']} *Developer:* @TollipopBot\n"
        f"{EMOJIS['domain']} *Domains Available:* {len(DOMAINS)}\n"
        f"{EMOJIS['users']} *Total Users:* {total_users}\n"
        f"{EMOJIS['users']} *Active Users:* {active_users}\n\n"
        f"{EMOJIS['success']} Fast and reliable account generation\n"
        f"{EMOJIS['success']} Secure and private\n"
        f"{EMOJIS['success']} Regular database updates",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def help_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    keyboard = [[InlineKeyboardButton(f"{EMOJIS['back']} Main Menu", callback_data="main_menu")]]
    
    await query.edit_message_text(
        f"{EMOJIS['help']} *Help Center* {EMOJIS['help']}\n\n"
        f"{EMOJIS['success']} */start* - Show main menu\n"
        f"{EMOJIS['success']} */key <key>* - Redeem your access key\n"
        f"{EMOJIS['success']} Use the generate button to get accounts\n\n"
        f"{EMOJIS['warning']} *How to use:*\n"
        "1. Get an access key from admin\n"
        "2. Redeem it using /key command\n"
        "3. Use the generate button to get accounts\n\n"
        f"{EMOJIS['error']} *Important:*\n"
        "• Don't share your key with others\n"
        "• Report any issues to admin",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def feedback_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    keyboard = [[InlineKeyboardButton(f"{EMOJIS['back']} Main Menu", callback_data="main_menu")]]
    
    await query.edit_message_text(
        f"{EMOJIS['feedback']} *Feedback*\n\n"
        "Please send your feedback, suggestions or bug reports.\n\n"
        "Just type your message and send it, it will be forwarded to the admin.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return AWAITING_FEEDBACK

async def handle_feedback(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if is_banned(user_id):
        return await update.message.reply_text(
            f"{EMOJIS['error']} You have been banned from using this bot."
        )
    
    feedback = update.message.text
    username = update.effective_user.username or "N/A"
    
    with open(FEEDBACK_FILE, "a", encoding="utf-8") as f:
        f.write(f"User: {user_id} (@{username})\nFeedback: {feedback}\n\n")
    
    keyboard = [[InlineKeyboardButton(f"{EMOJIS['back']} Main Menu", callback_data="main_menu")]]
    
    await update.message.reply_text(
        f"{EMOJIS['success']} *Thank you for your feedback!*\n\n"
        "Your message has been sent to the admin.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    # Notify admin
    try:
        await context.bot.send_message(
            ADMIN_ID,
            f"{EMOJIS['feedback']} *New Feedback*\n\n"
            f"{EMOJIS['users']} User: {user_id} (@{username})\n"
            f"{EMOJIS['feedback']} Message: {feedback}",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Error sending feedback to admin: {str(e)}")
    
    return ConversationHandler.END

async def admin_stats(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return await query.edit_message_text(
            f"{EMOJIS['error']} You are not authorized to use this feature!"
        )
    
    total_users = len(keys_data["user_keys"])
    active_users = sum(1 for expiry in keys_data["user_keys"].values() 
                   if expiry is None or datetime.now().timestamp() < expiry)
    expired_users = total_users - active_users
    
    # Count banned users
    banned_users = 0
    if os.path.exists(BANNED_USERS_FILE):
        with open(BANNED_USERS_FILE, "r") as f:
            banned_users = len(f.read().splitlines())
    
    keyboard = [[InlineKeyboardButton(f"{EMOJIS['back']} Admin Panel", callback_data="main_admin")]]
    
    await query.edit_message_text(
        f"{EMOJIS['stats']} *Admin Statistics*\n\n"
        f"{EMOJIS['users']} Total Users: `{total_users}`\n"
        f"{EMOJIS['success']} Active Users: `{active_users}`\n"
        f"{EMOJIS['error']} Expired Users: `{expired_users}`\n"
        f"{EMOJIS['key']} Available Keys: `{len(keys_data['keys'])}`\n"
        f"{EMOJIS['domain']} Domains: `{len(DOMAINS)}`\n"
        f"{EMOJIS['ban']} Banned Users: `{banned_users}`",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def broadcast_message(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return await query.edit_message_text(
            f"{EMOJIS['error']} You are not authorized to use this feature!"
        )
    
    await query.edit_message_text(
        f"{EMOJIS['broadcast']} *Broadcast Message*\n\n"
        "Please reply with the message you want to broadcast to all users.",
        parse_mode="Markdown"
    )
    return AWAITING_BROADCAST

async def handle_broadcast(update: Update, context: CallbackContext):
    message = update.message.text
    users = list(keys_data["user_keys"].keys())
    success = 0
    failed = 0
    
    processing_msg = await update.message.reply_text(
        f"{EMOJIS['broadcast']} Sending broadcast messages to {len(users)} users..."
    )
    
    for user_id in users:
        try:
            await context.bot.send_message(
                chat_id=int(user_id),
                text=f"{EMOJIS['broadcast']} *Broadcast Message*\n\n{message}",
                parse_mode="Markdown"
            )
            success += 1
        except Exception as e:
            print(f"Error sending to {user_id}: {str(e)}")
            failed += 1
        await asyncio.sleep(0.1)
    
    keyboard = [[InlineKeyboardButton(f"{EMOJIS['back']} Admin Panel", callback_data="main_admin")]]
    
    await processing_msg.edit_text(
        f"{EMOJIS['success']} *Broadcast Completed!*\n\n"
        f"{EMOJIS['success']} Success: `{success}`\n"
        f"{EMOJIS['error']} Failed: `{failed}`",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def ban_user(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return await query.edit_message_text(
            f"{EMOJIS['error']} You are not authorized to use this feature!"
        )
    
    await query.edit_message_text(
        f"{EMOJIS['ban']} *Ban User*\n\n"
        "Please reply with the user ID you want to ban.",
        parse_mode="Markdown"
    )
    return AWAITING_BAN_USER

async def handle_ban_user(update: Update, context: CallbackContext):
    user_id = update.message.text.strip()
    
    if not user_id.isdigit():
        keyboard = [[InlineKeyboardButton(f"{EMOJIS['back']} Admin Panel", callback_data="main_admin")]]
        await update.message.reply_text(
            f"{EMOJIS['error']} Invalid user ID! Please enter a numeric user ID.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    
    with open(BANNED_USERS_FILE, "a") as f:
        f.write(f"{user_id}\n")
    
    keyboard = [[InlineKeyboardButton(f"{EMOJIS['back']} Admin Panel", callback_data="main_admin")]]
    
    await update.message.reply_text(
        f"{EMOJIS['success']} User `{user_id}` has been banned.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Operation cancelled.",
        reply_markup=create_main_menu()
    )
    return ConversationHandler.END

# === MAIN FUNCTION ===
def main():
    # Create updater
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher
    
    # Add command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("key", redeem_key))
    
    # Add callback query handlers
    dispatcher.add_handler(CallbackQueryHandler(generate_menu, pattern="^main_generate$"))
    dispatcher.add_handler(CallbackQueryHandler(bot_info, pattern="^main_info$"))
    dispatcher.add_handler(CallbackQueryHandler(help_menu, pattern="^main_help$"))
    dispatcher.add_handler(CallbackQueryHandler(feedback_menu, pattern="^main_feedback$"))
    dispatcher.add_handler(CallbackQueryHandler(admin_panel, pattern="^main_admin$"))
    dispatcher.add_handler(CallbackQueryHandler(main_menu_handler, pattern="^main_menu$"))
    dispatcher.add_handler(CallbackQueryHandler(generate_filtered_accounts, pattern="^generate_"))
    
    # Admin handlers
    dispatcher.add_handler(CallbackQueryHandler(admin_stats, pattern="^admin_stats$"))
    dispatcher.add_handler(CallbackQueryHandler(generate_key_menu, pattern="^admin_genkey$"))
    dispatcher.add_handler(CallbackQueryHandler(generate_key, pattern="^genkey_"))
    dispatcher.add_handler(CallbackQueryHandler(broadcast_message, pattern="^admin_broadcast$"))
    dispatcher.add_handler(CallbackQueryHandler(ban_user, pattern="^admin_ban$"))
    
    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(broadcast_message, pattern="^admin_broadcast$"),
            CallbackQueryHandler(ban_user, pattern="^admin_ban$"),
            CallbackQueryHandler(feedback_menu, pattern="^main_feedback$")
        ],
        states={
            AWAITING_BROADCAST: [MessageHandler(Filters.text & ~Filters.command, handle_broadcast)],
            AWAITING_BAN_USER: [MessageHandler(Filters.text & ~Filters.command, handle_ban_user)],
            AWAITING_FEEDBACK: [MessageHandler(Filters.text & ~Filters.command, handle_feedback)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    
    dispatcher.add_handler(conv_handler)
    
    print("🤖 Tollipop Bot is starting...")
    print("✅ Bot is running and waiting for messages...")
    
    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
