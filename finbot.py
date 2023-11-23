#!/usr/bin/env python
# pylint: disable=unused-argument, wrong-import-position
# This program is dedicated to the public domain under the CC0 license.

"""
First, a few callback functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""


import logging
from dotenv import load_dotenv
load_dotenv()

from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

import requests

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update,KeyboardButton,InlineKeyboardMarkup,InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
import crud
import re
import os 
from database import session
import service


bot_token = os.getenv('BOT_TOKEN')



# Enable logging
logger = logging.getLogger(__name__)

TELEGRAMID= range(1)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks the user about their gender."""
    reply_keyboard = [[KeyboardButton(text='Поделиться контактом', request_contact=True)]]
    user_id = update.message.from_user.id
    await update.message.reply_text(
        f"🧑‍💻Здравствуйте {update.message.from_user.first_name}.👋\nДанный бот предназначен для оформления заявок финансового отдела по согласованию оплат.\n\n your user id is {user_id} \nplease give this to admin",
    )

    return TELEGRAMID


async def phonenumber(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the selected gender and asks for a photo."""
    user_id = update.message.from_user.id
    await update.message.reply_text(
        f"Your user id is {user_id}\nplease give this to admin in order to use."
    )

    return TELEGRAMID









async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    await update.message.reply_text(
        "Bye", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END



status_filte = {'accepted':1,'denied':2}

response_data = {'denied':'Оплата не утверждена ❌','accepted':'Спасибо,вы согласовали оплату✅'}

async def handle_callback_query(update:Update, context: ContextTypes.DEFAULT_TYPE):
    
    query = update.callback_query
    selected_option = query.data
    reply_markup = InlineKeyboardMarkup([])
    message = query.message
    text_of_order = query.message.text
    user_id = query.from_user.id
    chat_id = message.chat_id
    message_id = message.message_id
    order_id = list(map(int, re.findall('\d+', text_of_order)))[0]
    user = crud.get_user(db=session,tg_id=user_id)
    is_owner = crud.get_history(db=session,user_id=user.id,order_id=order_id)
    if is_owner.status!=0 or user.id!=is_owner.user_id:
        await context.bot.delete_message(chat_id=chat_id,message_id=message_id)
        await query.edit_message_text(text=text_of_order,reply_markup=InlineKeyboardMarkup([[]]))
        await query.message.reply_text('Вы уже проголосовали ✅')
    else:
        history = crud.history_update(db=session,history_id=is_owner.id,status=status_filte[selected_option])
        if history.status==1:
            users = crud.get_sphere_user(db=session,order_id=history.order_id,sphere_id=history.hi_order.sphere_id)
            if users:
                crud.history_create(db=session,user_id=users.user_id,order_id=history.order_id)
                order = crud.order_get_with_id(db=session,order_id=history.order_id)
                message = f"Заявка #{order.id}s\n🔘Тип: {order.order_sp.name}\n🙍‍♂Заказчик: {order.purchaser}\n📦Товар: {order.title}\n👨‍💼Поставщик: {order.supplier}\n💰Стоимость: {order.price} UZS\n💲Тип оплаты: {payment_type[order.payment_type]}\n💳Плательщик: {order.order_py.name}\nℹ️Описание: {order.comment}\nСрочно: {is_urgent[order.is_urgent]}"
                try:
                    service.sendtotelegram(bot_token=bot_token,chat_id=users.sp_user.tg_id,message_text=message)
                except:
                    pass
            else:
                crud.order_status_update(db=session,order_id=history.order_id,status=1)
        else:
            crud.order_status_update(db=session,order_id=history.order_id,status=2)
        await query.edit_message_text(text=text_of_order+f"\n\n{response_data[selected_option]}",reply_markup=InlineKeyboardMarkup([[]]))
    #if order_update.status_code == 200: 
    #    await context.bot.delete_message(chat_id=chat_id,message_id=message_id)
    #    if selected_option == 'accepted':
    #        await query.message.reply_text('Спасибо,вы согласовали оплату✅')
    #    else:
    #        await query.message.reply_text('Оплата не утверждена ❌')
    #else:
    #    await context.bot.delete_message(chat_id=chat_id,message_id=message_id)
    #    await query.message.reply_text('Вы уже проголосовали ✅')
        



def main() -> None:
    callback_query_handler = CallbackQueryHandler(handle_callback_query)
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(bot_token).build()
    application.add_handler(callback_query_handler)

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            TELEGRAMID: [MessageHandler(filters.CONTACT, phonenumber)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],


    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()