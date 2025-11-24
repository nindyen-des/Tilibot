import os
import json
import random
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackContext,
    CallbackQueryHandler,
    MessageHandler,
    filters,
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
LINES_TO_SEND = 100
PORT = int(os.environ.get('PORT', 8080))

# === STATES FOR CONVERSATION HANDLERS ===
AWAITING_USER_ID, AWAITING_SEARCH_QUERY, AWAITING_BROADCAST, AWAITING_ANNOUNCEMENT = range(4)
AWAITING_BAN_USER, AWAITING_UNBAN_USER, AWAITING_NEW_DOMAIN, AWAITING_FEEDBACK = range(4, 8)

# === DOMAIN LIST ===
DOMAINS = [
    "100082", "authgop", "mtacc", "garena", "roblox", "gaslite", "mobilelegends",
    "pubg", "codashop", "facebook", "Instagram", "netflix", "tiktok",
    "telegram", "freefire", "bloodstrike", "freefire", "warzone"
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
    "search": "🔎",
    "broadcast": "📢",
    "announce": "📌",
    "ban": "🚫",
    "unban": "✅",
    "add": "➕",
    "remove": "➖",
    "clear": "🔄",
    "users": "👥",
    "logs": "📋",
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
        "1m": 60, "5m": 300,
        "1h": 3600, "1d": 86400, "3d": 259200, "7d": 604800,
        "15d": 1296000, "30d": 2592000
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
        [InlineKeyboardButton(f"{EMOJIS['time']} My Time", callback_data="main_time"),
         InlineKeyboardButton(f"{EMOJIS['stats']} Stats", callback_data="main_stats")],
        [InlineKeyboardButton(f"{EMOJIS['feedback']} Feedback", callback_data="main_feedback"),
         InlineKeyboardButton(f"{EMOJIS['key']} Redeem Key", callback_data="main_redeem")]
    ]
    
    if is_admin(ADMIN_ID):
        keyboard.append([InlineKeyboardButton(f"{EMOJIS['admin']} ADMIN PANEL", callback_data="main_admin")])
    
    return InlineKeyboardMarkup(keyboard)

def create_admin_menu():
    keyboard = [
        [InlineKeyboardButton(f"{EMOJIS['logs']} Logs", callback_data="admin_logs"),
         InlineKeyboardButton(f"{EMOJIS['stats']} Stats", callback_data="admin_stats")],
        [InlineKeyboardButton(f"{EMOJIS['key']} Generate Key", callback_data="admin_genkey"),
         InlineKeyboardButton(f"{EMOJIS['time']} User Time", callback_data="admin_usertime")],
        [InlineKeyboardButton(f"{EMOJIS['broadcast']} Broadcast", callback_data="admin_broadcast"),
         InlineKeyboardButton(f"{EMOJIS['announce']} Announcement", callback_data="admin_announce")],
        [InlineKeyboardButton(f"{EMOJIS['ban']} Ban User", callback_data="admin_ban"),
         InlineKeyboardButton(f"{EMOJIS['unban']} Unban User", callback_data="admin_unban")],
        [InlineKeyboardButton(f"{EMOJIS['add']} Add Domain", callback_data="admin_adddomain"),
         InlineKeyboardButton(f"{EMOJIS['remove']} Remove Domain", callback_data="admin_removedomain")],
        [InlineKeyboardButton(f"{EMOJIS['search']} Search Accounts", callback_data="admin_search"),
         InlineKeyboardButton(f"{EMOJIS['clear']} Clear Used", callback_data="admin_clearused")],
        [InlineKeyboardButton(f"{EMOJIS['users']} User List", callback_data="admin_userlist")],
        [InlineKeyboardButton(f"{EMOJIS['back']} Main Menu", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_key_duration_menu():
    keyboard = [
        [InlineKeyboardButton("1 Minute", callback_data="genkey_1m"),
         InlineKeyboardButton("5 Minutes", callback_data="genkey_5m")],
        [InlineKeyboardButton("1 Hour", callback_data="genkey_1h"),
         InlineKeyboardButton("1 Day", callback_data="genkey_1d")],
        [InlineKeyboardButton("3 Days", callback_data="genkey_3d"),
         InlineKeyboardButton("7 Days", callback_data="genkey_7d")],
        [InlineKeyboardButton("15 Days", callback_data="genkey_15d"),
         InlineKeyboardButton("30 Days", callback_data="genkey_30d")],
        [InlineKeyboardButton("Lifetime", callback_data="genkey_lifetime")],
        [InlineKeyboardButton(f"{EMOJIS['back']} Admin Panel", callback_data="main_admin")]
    ]
    return InlineKeyboardMarkup(keyboard)

# === COMMAND HANDLERS ===
async def start(update: Update, context: CallbackContext):
    if is_banned(update.message.chat_id):
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
    if is_banned(update.message.chat_id):
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

    chat_id = str(update.message.chat_id)
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
    chat_id = str(query.message.chat_id)
    
    if is_banned(query.message.chat_id):
        return await query.message.reply_text(
            f"{EMOJIS['error']} You have been banned from using this bot."
        )
    
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
    chat_id, selected_domain = str(query.message.chat_id), query.data.replace("generate_", "")

    if is_banned(query.message.chat_id):
        return await query.message.reply_text(
            f"{EMOJIS['error']} You have been banned from using this bot."
        )
    
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

    # Find matching lines FAST
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

    filename = f"PREMIUM_{selected_domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, "w", encoding="utf-8", errors="ignore") as f:
        f.write(f"🔥 𝗚𝗘𝗡𝗘𝗥𝗔𝗧𝗘𝗗 𝗕𝗬 𝗧𝗢𝗟𝗟𝗜𝗣𝗢𝗣 𝗙𝗥𝗘𝗘 𝗕𝗢𝗧\n")
        f.write(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"🌐 Domain: {selected_domain}\n")
        f.write(f"📦 Total Accounts: {len(matched_lines)}\n\n")
        f.write("\n".join(matched_lines))

    await asyncio.sleep(2)  # Strict 2-second delay

    await processing_msg.delete()
    try:
        with open(filename, "rb") as f:
            await query.message.reply_document(
                document=InputFile(f, filename=filename),
                caption=(
                    f"{EMOJIS['success']} *PREMIUM {selected_domain.upper()} ACCOUNTS*\n\n"
                    f"📦 *Total Accounts:* {len(matched_lines)}\n"
                    f"⏳ *Generated At:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    f"🔹 *NOTE:* Please use responsibly!"
                ),
                parse_mode="Markdown"
            )
    except Exception as e:
        await query.message.reply_text(
            f"{EMOJIS['error']} Error sending file: {str(e)}"
        )
        return

    os.remove(filename)

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

async def view_logs(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return await query.edit_message_text(
            f"{EMOJIS['error']} You are not authorized to use this feature!"
        )
    
    if not keys_data["user_keys"]:
        return await query.edit_message_text(
            f"{EMOJIS['warning']} No users have redeemed keys yet."
        )

    log_text = f"{EMOJIS['logs']} *Redeemed Keys Log:*\n\n"
    for user, expiry in keys_data["user_keys"].items():
        expiry_text = "Lifetime" if expiry is None else format_time(expiry)
        log_text += f"👤 `{user}` - ⏳ `{expiry_text}`\n"

    keyboard = [[InlineKeyboardButton(f"{EMOJIS['back']} Admin Panel", callback_data="main_admin")]]
    
    await query.edit_message_text(
        log_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
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
        f"{EMOJIS['success']} *Version:* 3.0 Premium\n"
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
        f"{EMOJIS['success']} */generate* - Generate premium accounts\n\n"
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

async def user_time(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    chat_id = str(query.message.chat_id)
    
    if chat_id not in keys_data["user_keys"]:
        keyboard = [[InlineKeyboardButton(f"{EMOJIS['back']} Main Menu", callback_data="main_menu")]]
        return await query.edit_message_text(
            f"{EMOJIS['error']} *No Active Key Found!*\n\n"
            "You need to redeem a key first to check your time.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    expiry = keys_data["user_keys"][chat_id]
    expiry_text = "Lifetime" if expiry is None else format_time(expiry)
    
    keyboard = [
        [InlineKeyboardButton(f"{EMOJIS['back']} Main Menu", callback_data="main_menu")],
        [InlineKeyboardButton(f"{EMOJIS['generate']} Generate Accounts", callback_data="main_generate")]
    ]
    
    await query.edit_message_text(
        f"{EMOJIS['time']} *Your Account Status*\n\n"
        f"{EMOJIS['success']} User ID: `{chat_id}`\n"
        f"{EMOJIS['success']} Active: `Yes`\n"
        f"{EMOJIS['time']} Expires: `{expiry_text}`",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def stats(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    total_users = len(keys_data["user_keys"])
    active_users = sum(1 for expiry in keys_data["user_keys"].values() 
                   if expiry is None or datetime.now().timestamp() < expiry)
    expired_users = total_users - active_users
    
    keyboard = [[InlineKeyboardButton(f"{EMOJIS['back']} Main Menu", callback_data="main_menu")]]
    
    await query.edit_message_text(
        f"{EMOJIS['stats']} *Bot Statistics*\n\n"
        f"{EMOJIS['users']} Total Users: `{total_users}`\n"
        f"{EMOJIS['success']} Active Users: `{active_users}`\n"
        f"{EMOJIS['error']} Expired Users: `{expired_users}`\n"
        f"{EMOJIS['key']} Available Keys: `{len(keys_data['keys'])}`\n"
        f"{EMOJIS['domain']} Domains: `{len(DOMAINS)}`",
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
    if is_banned(update.message.chat_id):
        return await update.message.reply_text(
            f"{EMOJIS['error']} You have been banned from using this bot."
        )
    
    feedback = update.message.text
    user_id = update.message.chat_id
    username = update.message.from_user.username or "N/A"
    
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

async def user_time_admin(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return await query.edit_message_text(
            f"{EMOJIS['error']} You are not authorized to use this feature!"
        )
    
    await query.edit_message_text(
        f"{EMOJIS['time']} *Check User Time*\n\n"
        "Please reply with the user ID you want to check.\n\n"
        "Example: `123456789`",
        parse_mode="Markdown"
    )
    return AWAITING_USER_ID

async def handle_user_time_check(update: Update, context: CallbackContext):
    user_id = update.message.text.strip()
    chat_id = str(update.message.chat_id)
    
    if not user_id.isdigit():
        keyboard = [[InlineKeyboardButton(f"{EMOJIS['back']} Admin Panel", callback_data="main_admin")]]
        await update.message.reply_text(
            f"{EMOJIS['error']} Invalid user ID! Please enter a numeric user ID.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return
    
    if user_id not in keys_data["user_keys"]:
        keyboard = [[InlineKeyboardButton(f"{EMOJIS['back']} Admin Panel", callback_data="main_admin")]]
        await update.message.reply_text(
            f"{EMOJIS['error']} User `{user_id}` doesn't have an active key.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return
    
    expiry = keys_data["user_keys"][user_id]
    expiry_text = "Lifetime" if expiry is None else format_time(expiry)
    
    keyboard = [[InlineKeyboardButton(f"{EMOJIS['back']} Admin Panel", callback_data="main_admin")]]
    
    await update.message.reply_text(
        f"{EMOJIS['time']} *User Time Info*\n\n"
        f"{EMOJIS['users']} User ID: `{user_id}`\n"
        f"{EMOJIS['time']} Expires: `{expiry_text}`",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def search_accounts(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return await query.edit_message_text(
            f"{EMOJIS['error']} You are not authorized to use this feature!"
        )
    
    await query.edit_message_text(
        f"{EMOJIS['search']} *Search Accounts*\n\n"
        "Please reply with the search keyword and number of lines (optional) in this format:\n\n"
        "`<keyword> <lines>`\n\n"
        "Example: `garena 100`",
        parse_mode="Markdown"
    )
    return AWAITING_SEARCH_QUERY

async def handle_search_query(update: Update, context: CallbackContext):
    query = update.message.text.strip()
    parts = query.split()
    
    if len(parts) < 1:
        keyboard = [[InlineKeyboardButton(f"{EMOJIS['back']} Admin Panel", callback_data="main_admin")]]
        await update.message.reply_text(
            f"{EMOJIS['error']} Invalid format! Please use: `<keyword> <lines>`",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    
    keyword = parts[0]
    lines = 100 if len(parts) < 2 else int(parts[1]) if parts[1].isdigit() else 100
    
    processing_msg = await update.message.reply_text(
        f"{EMOJIS['search']} Searching for `{keyword}` (max {lines} lines)..."
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
        if len(matched_lines) >= lines:
            break
        try:
            with open(db_file, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    stripped_line = line.strip()
                    if keyword.lower() in stripped_line.lower() and stripped_line not in used_accounts:
                        matched_lines.append(stripped_line)
                        if len(matched_lines) >= lines:
                            break
        except Exception as e:
            print(f"Error reading {db_file}: {str(e)}")
            continue

    if not matched_lines:
        await processing_msg.delete()
        keyboard = [[InlineKeyboardButton(f"{EMOJIS['back']} Admin Panel", callback_data="main_admin")]]
        await update.message.reply_text(
            f"{EMOJIS['error']} No accounts found for keyword `{keyword}`",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    filename = f"SEARCH_{keyword}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, "w", encoding="utf-8", errors="ignore") as f:
        f.write(f"🔍 Search Results\n")
        f.write(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"🔎 Keyword: {keyword}\n")
        f.write(f"📦 Total Found: {len(matched_lines)}\n\n")
        f.write("\n".join(matched_lines[:lines]))

    await processing_msg.delete()
    
    try:
        with open(filename, "rb") as f:
            await update.message.reply_document(
                document=InputFile(f, filename=filename),
                caption=(
                    f"{EMOJIS['success']} *Search Results*\n\n"
                    f"{EMOJIS['search']} Keyword: `{keyword}`\n"
                    f"{EMOJIS['users']} Accounts Found: `{len(matched_lines)}`\n"
                    f"{EMOJIS['time']} Search Time: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"
                ),
                parse_mode="Markdown"
            )
    except Exception as e:
        keyboard = [[InlineKeyboardButton(f"{EMOJIS['back']} Admin Panel", callback_data="main_admin")]]
        await update.message.reply_text(
            f"{EMOJIS['error']} Error sending file: {str(e)}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    os.remove(filename)
    return ConversationHandler.END

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
    users = keys_data["user_keys"].keys()
    success = 0
    failed = 0
    
    processing_msg = await update.message.reply_text(
        f"{EMOJIS['broadcast']} Sending broadcast messages..."
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

async def announcement_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return await query.edit_message_text(
            f"{EMOJIS['error']} You are not authorized to use this feature!"
        )
    
    await query.edit_message_text(
        f"{EMOJIS['announce']} *Create Announcement*\n\n"
        "Please reply with the announcement message you want to pin.",
        parse_mode="Markdown"
    )
    return AWAITING_ANNOUNCEMENT

async def handle_announcement(update: Update, context: CallbackContext):
    message = update.message.text
    
    keyboard = [[InlineKeyboardButton(f"{EMOJIS['back']} Admin Panel", callback_data="main_admin")]]
    
    await update.message.reply_text(
        f"{EMOJIS['announce']} *Announcement*\n\n{message}",
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

async def unban_user(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return await query.edit_message_text(
            f"{EMOJIS['error']} You are not authorized to use this feature!"
        )
    
    await query.edit_message_text(
        f"{EMOJIS['unban']} *Unban User*\n\n"
        "Please reply with the user ID you want to unban.",
        parse_mode="Markdown"
    )
    return AWAITING_UNBAN_USER

async def handle_unban_user(update: Update, context: CallbackContext):
    user_id = update.message.text.strip()
    
    if not user_id.isdigit():
        keyboard = [[InlineKeyboardButton(f"{EMOJIS['back']} Admin Panel", callback_data="main_admin")]]
        await update.message.reply_text(
            f"{EMOJIS['error']} Invalid user ID! Please enter a numeric user ID.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    
    if not os.path.exists(BANNED_USERS_FILE):
        keyboard = [[InlineKeyboardButton(f"{EMOJIS['back']} Admin Panel", callback_data="main_admin")]]
        await update.message.reply_text(
            f"{EMOJIS['error']} No users are currently banned.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    
    with open(BANNED_USERS_FILE, "r") as f:
        banned_users = f.read().splitlines()
    
    if user_id not in banned_users:
        keyboard = [[InlineKeyboardButton(f"{EMOJIS['back']} Admin Panel", callback_data="main_admin")]]
        await update.message.reply_text(
            f"{EMOJIS['error']} User `{user_id}` is not banned.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    
    banned_users.remove(user_id)
    with open(BANNED_USERS_FILE, "w") as f:
        f.write("\n".join(banned_users))
    
    keyboard = [[InlineKeyboardButton(f"{EMOJIS['back']} Admin Panel", callback_data="main_admin")]]
    
    await update.message.reply_text(
        f"{EMOJIS['success']} User `{user_id}` has been unbanned.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def add_domain(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return await query.edit_message_text(
            f"{EMOJIS['error']} You are not authorized to use this feature!"
        )
    
    await query.edit_message_text(
        f"{EMOJIS['add']} *Add Domain*\n\n"
        "Please reply with the new domain you want to add.",
        parse_mode="Markdown"
    )
    return AWAITING_NEW_DOMAIN

async def handle_add_domain(update: Update, context: CallbackContext):
    new_domain = update.message.text.strip().lower()
    
    if new_domain in DOMAINS:
        keyboard = [[InlineKeyboardButton(f"{EMOJIS['back']} Admin Panel", callback_data="main_admin")]]
        await update.message.reply_text(
            f"{EMOJIS['error']} Domain `{new_domain}` already exists.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    
    DOMAINS.append(new_domain)
    
    keyboard = [[InlineKeyboardButton(f"{EMOJIS['back']} Admin Panel", callback_data="main_admin")]]
    
    await update.message.reply_text(
        f"{EMOJIS['success']} Domain `{new_domain}` has been added.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def remove_domain(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return await query.edit_message_text(
            f"{EMOJIS['error']} You are not authorized to use this feature!"
        )
    
    keyboard = []
    for i in range(0, len(DOMAINS), 2):
        row = []
        if i < len(DOMAINS):
            row.append(InlineKeyboardButton(DOMAINS[i], callback_data=f"remove_{DOMAINS[i]}"))
        if i+1 < len(DOMAINS):
            row.append(InlineKeyboardButton(DOMAINS[i+1], callback_data=f"remove_{DOMAINS[i+1]}"))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton(f"{EMOJIS['back']} Admin Panel", callback_data="main_admin")])
    
    await query.edit_message_text(
        f"{EMOJIS['remove']} *Remove Domain*\n\n"
        "Select the domain you want to remove:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def handle_remove_domain(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return await query.edit_message_text(
            f"{EMOJIS['error']} You are not authorized to use this feature!"
        )
    
    domain = query.data.replace("remove_", "")
    DOMAINS.remove(domain)
    
    keyboard = [[InlineKeyboardButton(f"{EMOJIS['back']} Admin Panel", callback_data="main_admin")]]
    
    await query.edit_message_text(
        f"{EMOJIS['success']} Domain `{domain}` has been removed.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def clear_used(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return await query.edit_message_text(
            f"{EMOJIS['error']} You are not authorized to use this feature!"
        )
    
    open(USED_ACCOUNTS_FILE, "w").close()
    
    keyboard = [[InlineKeyboardButton(f"{EMOJIS['back']} Admin Panel", callback_data="main_admin")]]
    
    await query.edit_message_text(
        f"{EMOJIS['success']} Used accounts database has been cleared.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def user_list(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return await query.edit_message_text(
            f"{EMOJIS['error']} You are not authorized to use this feature!"
        )
    
    if not keys_data["user_keys"]:
        keyboard = [[InlineKeyboardButton(f"{EMOJIS['back']} Admin Panel", callback_data="main_admin")]]
        return await query.edit_message_text(
            f"{EMOJIS['warning']} No users have redeemed keys yet.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    users = []
    for user_id, expiry in keys_data["user_keys"].items():
        expiry_text = "Lifetime" if expiry is None else format_time(expiry)
        users.append(f"👤 `{user_id}` - ⏳ `{expiry_text}`")
    
    # Split into chunks of 50 users to avoid message length limit
    user_chunks = [users[i:i + 50] for i in range(0, len(users), 50)]
    
    keyboard = [[InlineKeyboardButton(f"{EMOJIS['back']} Admin Panel", callback_data="main_admin")]]
    
    for i, chunk in enumerate(user_chunks):
        await query.edit_message_text(
            f"{EMOJIS['users']} *User List* ({i+1}/{len(user_chunks)})\n\n" + "\n".join(chunk),
            reply_markup=InlineKeyboardMarkup(keyboard) if i == len(user_chunks)-1 else None,
            parse_mode="Markdown"
        )
        if i < len(user_chunks)-1:
            await asyncio.sleep(0.5)

async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Operation cancelled.",
        reply_markup=create_main_menu()
    )
    return ConversationHandler.END

# === MODIFIED MAIN FUNCTION FOR RENDER.COM ===
def main():
    app = Application.builder().token(TOKEN).build()
    
    # Add all handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("key", redeem_key))
    app.add_handler(CommandHandler("generate", generate_menu))
    
    # Callback query handlers
    app.add_handler(CallbackQueryHandler(generate_menu, pattern="^main_generate$"))
    app.add_handler(CallbackQueryHandler(bot_info, pattern="^main_info$"))
    app.add_handler(CallbackQueryHandler(help_menu, pattern="^main_help$"))
    app.add_handler(CallbackQueryHandler(user_time, pattern="^main_time$"))
    app.add_handler(CallbackQueryHandler(stats, pattern="^main_stats$"))
    app.add_handler(CallbackQueryHandler(feedback_menu, pattern="^main_feedback$"))
    app.add_handler(CallbackQueryHandler(admin_panel, pattern="^main_admin$"))
    app.add_handler(CallbackQueryHandler(main_menu_handler, pattern="^main_menu$"))
    app.add_handler(CallbackQueryHandler(generate_filtered_accounts, pattern="^generate_"))
    
    # Admin handlers
    app.add_handler(CallbackQueryHandler(view_logs, pattern="^admin_logs$"))
    app.add_handler(CallbackQueryHandler(admin_stats, pattern="^admin_stats$"))
    app.add_handler(CallbackQueryHandler(generate_key_menu, pattern="^admin_genkey$"))
    app.add_handler(CallbackQueryHandler(generate_key, pattern="^genkey_"))
    app.add_handler(CallbackQueryHandler(search_accounts, pattern="^admin_search$"))
    app.add_handler(CallbackQueryHandler(clear_used, pattern="^admin_clearused$"))
    app.add_handler(CallbackQueryHandler(user_list, pattern="^admin_userlist$"))
    app.add_handler(CallbackQueryHandler(handle_remove_domain, pattern="^remove_"))
    
    # Conversation handlers
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(user_time_admin, pattern="^admin_usertime$"),
            CallbackQueryHandler(broadcast_message, pattern="^admin_broadcast$"),
            CallbackQueryHandler(announcement_menu, pattern="^admin_announce$"),
            CallbackQueryHandler(ban_user, pattern="^admin_ban$"),
            CallbackQueryHandler(unban_user, pattern="^admin_unban$"),
            CallbackQueryHandler(add_domain, pattern="^admin_adddomain$"),
            CallbackQueryHandler(remove_domain, pattern="^admin_removedomain$"),
            CallbackQueryHandler(feedback_menu, pattern="^main_feedback$")
        ],
        states={
            AWAITING_USER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_time_check)],
            AWAITING_SEARCH_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search_query)],
            AWAITING_BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_broadcast)],
            AWAITING_ANNOUNCEMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_announcement)],
            AWAITING_BAN_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ban_user)],
            AWAITING_UNBAN_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unban_user)],
            AWAITING_NEW_DOMAIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_add_domain)],
            AWAITING_FEEDBACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_feedback)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    
    app.add_handler(conv_handler)
    
    print(f"🌟 𝗧𝗢𝗟𝗟𝗜𝗣𝗢𝗣 𝗙𝗥𝗘𝗘 𝗕𝗢𝗧 𝗜𝗦 𝗥𝗨𝗡𝗡𝗜𝗡𝗚...")
    
    # Use polling for both local and Render (simpler for free tier)
    app.run_polling()

if __name__ == "__main__":
    main()
