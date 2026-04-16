import telebot
from telebot import types
import sqlite3
from datetime import datetime
import os

# ================= CONFIGURATION =================
API_TOKEN = '8652193940:AAGlk4LFDe5kYI-HwHZyQtVIbpeJEH3KDnI'
BOT_USERNAME = "Gulidglorystore_robot" 
QR_IMAGE_FILE = 'pawan_qr.jpg' 
# =================================================

bot = telebot.TeleBot(API_TOKEN)
user_states = {}

def init_db():
    conn = sqlite3.connect('pkn_store.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, first_name TEXT, balance REAL DEFAULT 0.0, 
                       referrals INTEGER DEFAULT 0, total_earned REAL DEFAULT 0.0,
                       topped_up REAL DEFAULT 0.0, spent REAL DEFAULT 0.0,
                       purchases INTEGER DEFAULT 0, credits_bought INTEGER DEFAULT 0,
                       joined_date TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS stock 
                      (pack_id INTEGER PRIMARY KEY, credits INTEGER, stock_left INTEGER)''')
    cursor.execute('SELECT COUNT(*) FROM stock')
    if cursor.fetchone()[0] == 0:
        cursor.executemany('INSERT INTO stock VALUES (?, ?, ?)', [(1, 1, 76), (2, 2, 21), (3, 5, 9), (4, 10, 5)])
    cursor.execute('''CREATE TABLE IF NOT EXISTS referral_history 
                      (referrer_id INTEGER, referred_name TEXT, join_date TEXT)''')
    conn.commit()
    conn.close()

def get_user_data(user_id):
    conn = sqlite3.connect('pkn_store.db')
    cursor = conn.cursor()
    cursor.execute('SELECT balance, topped_up, spent, referrals, purchases, credits_bought, joined_date, total_earned FROM users WHERE user_id = ?', (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res

def get_live_stock():
    conn = sqlite3.connect('pkn_store.db')
    cursor = conn.cursor()
    cursor.execute('SELECT stock_left FROM stock ORDER BY pack_id')
    res = [row[0] for row in cursor.fetchall()]
    conn.close()
    return res

def main_menu(user_id, first_name):
    data = get_user_data(user_id)
    balance = data[0] if data else 0.0
    ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    text = (
        "╔══════════════════════╗\n"
        "  🎮 **Guild Glory Credit Shop**\n"
        "╚══════════════════════╝\n\n"
        f"👋 Welcome, **{first_name.upper()}**!\n\n"
        f"💵 **Wallet Balance:** ₹{balance:.2f}\n"
        f"🔗 **Referral Link:**\n{ref_link}\n\n"
        "💡 Earn ₹1 for every friend who joins!"
    )
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("➕ Add Balance", callback_data="add_balance"),
               types.InlineKeyboardButton("🎫 Buy Credits", callback_data="buy_credits"))
    markup.add(types.InlineKeyboardButton("👥 My Referrals", callback_data="my_referrals"),
               types.InlineKeyboardButton("📊 My Stats", callback_data="my_stats"))
    markup.add(types.InlineKeyboardButton("📞 Contact Admin         ↗️", url="https://t.me/deadly_cheatz"))
    return text, markup

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    init_db()
    conn = sqlite3.connect('pkn_store.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
    if cursor.fetchone() is None:
        join_date = datetime.now().strftime("%Y-%m-%d")
        args = message.text.split()
        referrer_id = args[1] if len(args) > 1 and args[1].isdigit() else None
        cursor.execute('INSERT INTO users (user_id, first_name, joined_date) VALUES (?, ?, ?)', (user_id, first_name, join_date))
        if referrer_id and int(referrer_id) != user_id:
            cursor.execute('UPDATE users SET balance = balance + 0.1, referrals = referrals + 1, total_earned = total_earned + 0.1 WHERE user_id = ?', (referrer_id,))
            cursor.execute('INSERT INTO referral_history VALUES (?, ?, ?)', (referrer_id, first_name, join_date))
            conn.commit()
            try: bot.send_message(referrer_id, f"🎊 **Live Referral Bonus!**\n{first_name} join hua, ₹1 add ho gaya!")
            except: pass
        else:
            conn.commit()
    conn.close()
    text, markup = main_menu(user_id, first_name)
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    user_id = call.from_user.id
    if call.data == "add_balance":
        user_states[user_id] = 'awaiting_amount'
        text = "➕ **Add Balance to Wallet**\n\nEnter the amount (₹) you want to add:\n(Minimum: ₹10)"
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("❌ Cancel", callback_data="back_to_menu"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    elif call.data == "buy_credits":
        d, s = get_user_data(user_id), get_live_stock()
        text = f"💳 **Buy Credits**\n\n💵 Balance: ₹{d[0]:.2f}\n💰 1 Credit = ₹90"
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton(f"✅ 1 Credits — ₹90 ({s[0]} left)", callback_data="buy_1"),
                   types.InlineKeyboardButton(f"✅ 2 Credits — ₹180 ({s[1]} left)", callback_data="buy_2"),
                   types.InlineKeyboardButton(f"✅ 5 Credits — ₹450 ({s[2]} left)", callback_data="buy_5"),
                   types.InlineKeyboardButton(f"✅ 10 Credits — ₹900 ({s[3]} left)", callback_data="buy_10"),
                   types.InlineKeyboardButton("⬅️ Back", callback_data="back_to_menu"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    elif call.data == "my_stats":
        d = get_user_data(user_id)
        text = f"📊 **Stats**\n\n💵 Balance: ₹{d[0]:.2f}\n💰 TopUp: ₹{d[1]:.2f}\n🛍️ Spent: ₹{d[2]:.2f}\n👥 Ref: {d[3]}\n📅 Joined: {d[6]}"
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅️ Back", callback_data="back_to_menu"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    elif call.data == "my_referrals":
        d = get_user_data(user_id)
        conn = sqlite3.connect('pkn_store.db')
        cursor = conn.cursor()
        cursor.execute('SELECT referred_name, join_date FROM referral_history WHERE referrer_id = ? ORDER BY rowid DESC LIMIT 15', (user_id,))
        rows = cursor.fetchall()
        conn.close()
        text = f"👥 **Referrals**\nTotal: {d[3]}\nEarned: ₹{d[7]:.2f}\n\nList:\n"
        for i, r in enumerate(rows, 1): text += f"{i}. {r[0]} ({r[1]})\n"
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅️ Back", callback_data="back_to_menu"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    elif call.data == "back_to_menu":
        user_states.pop(user_id, None)
        text, markup = main_menu(user_id, call.from_user.first_name)
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'awaiting_amount')
def process_amount(message):
    user_id = message.from_user.id
    if message.text.isdigit() and int(message.text) >= 10:
        amount = message.text
        user_states.pop(user_id, None)
        caption = f"✅ **Order Created for ₹{amount}**\n\nIs QR par payment karein."
        if os.path.exists(QR_IMAGE_FILE):
            with open(QR_IMAGE_FILE, 'rb') as f: bot.send_photo(message.chat.id, f, caption=caption)
        else: bot.send_message(message.chat.id, "⚠️ QR Missing!")
    else: bot.send_message(message.chat.id, "❌ Minimum ₹10!")

if __name__ == "__main__":
    init_db()
    print("--- Bot Start Ho Gaya Hai ---")
    bot.infinity_polling()  
