from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

async def handle_callback(client, callback_query: CallbackQuery, user_data, QUIZ):
    user_id = callback_query.from_user.id
    data = callback_query.data

    # Restart quiz
    if data in ("restart", "start_quiz"):
        try:
            await callback_query.message.delete()  # deletes the message containing the button
        except:
            pass
        # Delete all previous bot messages
        all_msgs = user_data.get(user_id, {}).get("all_msgs", [])
        for msg_id in all_msgs:
            try:
                await client.delete_messages(user_id, msg_id)
            except:
                pass

        user_data[user_id] = {"current_question": 0, "score": 0, "last_msg": None, "all_msgs": []}
        await callback_query.answer("Quiz restarted!", show_alert=False)
        return "restart"

    # End quiz early
    if data == "end_quiz":
        # Delete all bot messages
        all_msgs = user_data.get(user_id, {}).get("all_msgs", [])
        for msg_id in all_msgs:
            try:
                await client.delete_messages(user_id, msg_id)
            except:
                pass

        user_data[user_id]["all_msgs"] = []

        score = user_data[user_id]["score"]
        total = len(QUIZ)
        await callback_query.answer("Quiz ended!", show_alert=False)

        # Show final score with restart button
        buttons = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Restart Quiz", callback_data="restart")]]
        )
        msg = await client.send_message(
            user_id,
            f"Quiz ended early!\nYour score: {score} / {total}",
            reply_markup=buttons
        )
        # Store this message to allow deletion if restarted
        user_data[user_id]["all_msgs"].append(msg.id)
        return "ended"

    # Answer callback
    if data.startswith("ans"):
        _, q_index, selected = data.split(":")
        q_index = int(q_index)
        selected = int(selected)

        question = QUIZ[q_index]
        selected_option = question["options"][selected]
        correct_answer = question["answer"]

        if selected_option == correct_answer:
            user_data[user_id]["score"] += 1
            result = "✅ Correct!"
        else:
            result = f"❌ Wrong!\nCorrect answer: {correct_answer}"

        await callback_query.answer(result, show_alert=True)
        user_data[user_id]["current_question"] += 1
        return "answered"

    # Close button action
    if data == "close_button":
        try:
            await callback_query.message.delete()
            await callback_query.answer()
        except:
            pass
    return None


