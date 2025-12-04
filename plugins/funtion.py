import os, json, sys, asyncio
from config import Config
from pyrogram.enums import ParseMode
from pyrogram import filters, Client
from plugins.callback import handle_callback
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

user_data = {}

# Load quiz data
with open("data/data.json", "r") as f:
    DATA = json.load(f)
    QUIZ = DATA["questions"]



# /start command / welcome function
@Client.on_message(filters.command("start"))
async def start_quiz(client, message: Message):
    user_id = message.from_user.id

    # Delete all previous messages sent by bot ------------------------------------------
    state = user_data.get(user_id)
    if state and "all_msgs" in state:
        for msg_id in state["all_msgs"]:
            try:
                await client.delete_messages(user_id, msg_id)
            except:
                pass

    # The following code saves the user information in a json file (This can be used to broadcast ads later).-----------
    users_file = "data/users.json"
    # Ensure file exists
    if not os.path.exists(users_file):
        with open(users_file, "w") as json_file:
            json.dump([], json_file)

    # SAFE LOAD to avoid JSONDecodeError
    try:
        with open(users_file, "r") as json_file:
            users_data = json.load(json_file)
            if not isinstance(users_data, list):
                users_data = []
    except json.JSONDecodeError:
        users_data = []

    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    # Prepare user entry
    new_user = {
        "user_id": user_id,
        "username": username if username else None,
        "first_name": first_name if first_name else None
    }

    # Add user if not existing
    if not any(u["user_id"] == user_id for u in users_data):
        users_data.append(new_user)

        # Save back to JSON
        with open(users_file, "w") as json_file:
            json.dump(users_data, json_file, indent=4)


    # The following code will send the welcome message to the user
    user_data[user_id] = {"current_question": 0, "score": 0, "last_msg": None, "all_msgs": []}
    button = InlineKeyboardMarkup([[InlineKeyboardButton("Goto Quiz", callback_data="start_quiz"),
                                    InlineKeyboardButton(text="Close", callback_data="close_button")]])
    await message.reply(
        '<b>Hello.. {}</b>\nI\'m a Canadian G1 Licence Test Quiz bot made by '
        '<a href="https://github.com/m4mallu" target="_blank"><b>Renjith Rajan</b></a>'.format(
            message.from_user.first_name),
        reply_markup=button,
        parse_mode=ParseMode.HTML
    )


# Send questions to the user-----------------------------------------------------
async def send_question(client, user_id):
    q_index = user_data[user_id]["current_question"]

    if q_index >= len(QUIZ):

        # 1. Send initial calculating message
        calculating_msg = await client.send_message(
            user_id,
            "Calculating the score."
        )

        # 2. Simple 3-step animation
        for dots in [".", "..", "..."]:
            await asyncio.sleep(0.4)
            try:
                await calculating_msg.edit_text(f"Calculating the score{dots}")
            except:
                pass

        # 3. Delete all previous messages
        all_msgs = user_data[user_id].get("all_msgs", [])
        for msg_id in all_msgs:
            try:
                await client.delete_messages(user_id, msg_id)
            except:
                pass
        user_data[user_id]["all_msgs"] = []

        # 4. Gather score
        score = user_data[user_id]["score"]
        total = len(QUIZ)

        # 5. Buttons: Restart + Close
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("Start Quiz", callback_data="start_quiz")],
            [InlineKeyboardButton("Close", callback_data="close_button")]
        ])

        # Small delay for smoothness
        await asyncio.sleep(0.5)

        # 6. Edit message to final result
        await calculating_msg.edit_text(
            f"Quiz completed!\nYour Score: {score}/{total}",
            reply_markup=buttons
        )

        # Track final message
        user_data[user_id]["all_msgs"].append(calculating_msg.id)
        return

    # Delete previous question message
    last_msg = user_data[user_id].get("last_msg")
    if last_msg:
        try:
            await client.delete_messages(user_id, last_msg)
        except:
            pass

    question = QUIZ[q_index]
    progress = f"Question {q_index + 1} of {len(QUIZ)}"

    # Options buttons
    keyboard = [
        [InlineKeyboardButton(opt, callback_data=f"ans:{q_index}:{i}")]
        for i, opt in enumerate(question["options"])
    ]

    keyboard.append([
        InlineKeyboardButton("End Quiz", callback_data="end_quiz"),
        InlineKeyboardButton("Close", callback_data="close_button")
    ])

    # Handle string or list-type "question" field
    if isinstance(question["question"], list):
        question_text = "\n".join(question["question"])
    else:
        question_text = question["question"]

    # Send question photo + caption
    msg = await client.send_photo(
        user_id,
        photo=f"images/{question['image']}",
        caption=f"{progress}\n\n{question_text}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    user_data[user_id]["last_msg"] = msg.id
    user_data[user_id].setdefault("all_msgs", []).append(msg.id)


# This function provides some basic information about this bot (Admin use only)--------------------------------------
@Client.on_message(filters.command("about"))
async def about(_, message):
    text = (
        "🇨🇦 **About This Bot** 🇨🇦\n\n"
        "This Telegram bot helps you practice for the Ontario G1 driving test using image-based quiz questions.\n\n"
        "**Source Code & Contributions:**\n"
        "[GitHub Repository](https://github.com/m4mallu/G1LicenseBot)\n\n"
        "**Report Issues:**\n"
        "Please submit bugs or suggestions through the repository’s "
        "[Issues Page](https://github.com/m4mallu/G1LicenseBot/issues)\n\n"
        "Thank you for helping improve this project!"
    )
    close_button = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Close", callback_data="close_button")]]
    )
    await message.reply(
        text,
        disable_web_page_preview=True,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=close_button
    )
    await message.delete()


# This function counts total users of this bot (Admin use only)--------------------------------------
@Client.on_message(filters.command("users"))
async def user_counter(client, message: Message):

    _ = client

    user_id = message.from_user.id
    close_btn = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Close", callback_data="close_button")]]
    )

    # Check admin permission
    if user_id not in Config.ADMINS:
        await message.reply(
            "❌ You are not authorized\nto use this command ❌",
            reply_markup=close_btn
        )
        await message.delete()
        return

    users_file = "data/users.json"

    # If file missing or empty, count = 0
    if not os.path.exists(users_file):
        await message.reply(
            "👥 Total registered users: <b>0</b>",
            reply_markup=close_btn,
            parse_mode=ParseMode.HTML
        )
        return

    try:
        with open(users_file, "r") as json_file:
            users_data = json.load(json_file)
            if not isinstance(users_data, list):
                users_data = []
    except json.JSONDecodeError:
        users_data = []

    total_users = len(users_data)

    await message.reply(
        f"👥 Total registered users: <b>{total_users}</b>",
        reply_markup=close_btn,
        parse_mode=ParseMode.HTML
    )
    await message.delete()


# This function displays the total users of this bot (Admin use only)--------------------------------------
@Client.on_message(filters.command("listusers"))
async def list_users(client, message: Message):

    _ = client  # silence unused parameter warning
    max_length = 3900  # safe limit below Telegram's 4096 cap

    # --- CHECK IF USER IS ADMIN USING Config.ADMINS ---
    if message.from_user.id not in Config.ADMINS:
        close_btn = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Close", callback_data="close_button")]]
        )
        await message.reply(
            "❌ You are not authorized\nto use this command ❌",
            reply_markup=close_btn
        )
        return

    # --- Load JSON file ---
    users_file = "data/users.json"

    if not os.path.exists(users_file):
        await message.reply("No users found.")
        return

    try:
        with open(users_file, "r") as json_file:
            users_data = json.load(json_file)
            if not isinstance(users_data, list):
                users_data = []
    except json.JSONDecodeError:
        users_data = []

    if not users_data:
        await message.reply("No users found.")
        return

    # --- Build user list lines ---
    lines = []
    for user in users_data:
        first_name = user.get("first_name", "Unknown")
        username = user.get("username")

        if username:
            line = f"• <a href=\"https://t.me/{username}\">{first_name}</a>"
        else:
            line = f"• {first_name}"

        lines.append(line)

    # --- Split into multiple messages if too long ---
    messages = []
    current_block = ""

    for line in lines:
        if len(current_block) + len(line) + 2 > max_length:
            messages.append(current_block)
            current_block = line + "\n"
        else:
            current_block += line + "\n"

    if current_block.strip():
        messages.append(current_block)

    # --- Close button ---
    close_btn = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Close", callback_data="close_button")]]
    )

    # --- Send messages ---
    for block in messages:
        await message.reply(
            block,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=close_btn
        )
    await message.delete()


# This function broadcast messages to the bot users. (Admin use only)--------------------------------------
@Client.on_message(filters.command("broadcast"))
async def broadcast_message(client, message: Message):

    # Close button
    close_btn = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Close", callback_data="close_button")]]
    )

    # Admin check (only admins can broadcast)
    if message.from_user.id not in Config.ADMINS:
        await message.reply(
            "❌ You are not authorized\nto use this command ❌",
            reply_markup=close_btn
        )
        return

    # Extract broadcast text
    if len(message.command) < 2:
        await message.reply(
            "Usage:\n<b>/broadcast Your message here</b>",
            reply_markup=close_btn,
            parse_mode=ParseMode.HTML
        )
        return

    text = message.text.split(" ", 1)[1].strip()
    if not text:
        await message.reply("❌ Broadcast message is empty.",
                            reply_markup=close_btn,)
        return

    users_file = "data/users.json"

    # Ensure file exists
    if not os.path.exists(users_file):
        await message.reply("❌ No users found to broadcast.",
                            reply_markup=close_btn,)
        return

    # Safe load
    try:
        with open(users_file, "r") as json_file:
            users_data = json.load(json_file)
            if not isinstance(users_data, list):
                users_data = []
    except json.JSONDecodeError:
        users_data = []

    if not users_data:
        await message.reply("❌ No users found to broadcast.",
                            reply_markup=close_btn,)
        return

    sent = 0
    failed = 0

    # Broadcast to each user
    for user in users_data:
        try:
            await client.send_message(
                chat_id=user["user_id"],
                text=text,
                reply_markup=close_btn,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            sent += 1
        except:
            failed += 1
            continue

    # Summary for admin
    await message.reply(
        f"📢 <b>Broadcast completed</b>\n\n"
        f"✅ Sent to: <b>{sent}</b>\n"
        f"⚠️ Failed: <b>{failed}</b>",
        reply_markup=close_btn,
        parse_mode=ParseMode.HTML
    )
    await message.delete()


# This function restarts the bot users. (Admin use only)--------------------------------------
@Client.on_message(filters.command("reload"))
async def reload_bot(client, message: Message):

    _ = client
    # Close button
    close_btn = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Close", callback_data="close_button")]]
    )

    # --- ADMIN CHECK ---
    if message.from_user.id not in Config.ADMINS:
        await message.reply(
            "❌ You are not authorized\nto use this command ❌",
            reply_markup=close_btn
        )
        return

    # Send restarting message
    await message.reply(
        "🔄 <b>Bot is restarting...</b>",
        reply_markup=close_btn,
        parse_mode=ParseMode.HTML
    )
    await message.delete()

    # Restart the bot — no post-start message will be sent
    os.execv(sys.executable, [sys.executable] + sys.argv)


# Callback handler -------------------------------------------------
@Client.on_callback_query()
async def callback_handler(client, callback_query):
    user_id = callback_query.from_user.id
    try:
        action = await handle_callback(client, callback_query, user_data, QUIZ)
        if action in ["restart", "answered"]:
            await send_question(client, user_id)
    except:
        pass