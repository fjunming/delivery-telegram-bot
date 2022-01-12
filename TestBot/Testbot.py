#Libraries
import telegram
import logging
from datetime import datetime, timedelta
#import openpyxl #https://realpython.com/openpyxl-excel-spreadsheets-python/
import pytz
import html
import json
import traceback

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackQueryHandler,
    ConversationHandler,
    PicklePersistence,
)

#Files to import
import neworder

logging.basicConfig(filename='log.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

#========== Telegram Bot and Chat Settings ===================
token =
post_chat =
owner = 
admins = {}
log_chat =

#========== Outlet Settings, make sure every outlet entered is filled ===================
outlets = ["GORO Holland", "GORO Mapletree", "TSK Gambas Crescent", 'Jaisiam Singpost', 'Jaisiam Purvis',
           'Jaisiam Dhoby']

outlets_keyboard = [
    [InlineKeyboardButton("GORO Holland", callback_data='GORO Holland'),
     InlineKeyboardButton("GORO Mapletree", callback_data='GORO Mapletree')],
    [InlineKeyboardButton("TSK Gambas Crescent", callback_data='TSK Gambas Crescent'),
     InlineKeyboardButton("Jaisiam Singpost", callback_data='Jaisiam Singpost')],
    [InlineKeyboardButton("Jaisiam Purvis", callback_data='Jaisiam Purvis'),
     InlineKeyboardButton("Jaisiam Dhoby", callback_data='Jaisiam Dhoby')],
]

outletinfo = {'GORO Holland': '''Goro Japanese Cuisine
    43 Holland Drive
    Singapore 270043''',

'GORO Mapletree': '''Oh My Goro JAPANESE CUISINE
    20 Pasir Panjang road 
    # 02-21 maple tree business city S117439
    (Next to 7-Eleven)
    (Park at 20 East, post F10 to F16 area)''',

'TSK Gambas Crescent': '''Tai Shi Ke
    Nordcom 2, 28 Gambas Crescent, Level 3 Kitchen 11''',

'Jaisiam Singpost': '''Singpost Center, 10 Eunos Rd 8
# (placeholder), S408600
(Outlet Opposite NTUC Fairprice Cashier station, park at B2 zone K6 near travelator)''',

'Jaisiam Purvis': '''Purvis Street
S188604 (incomplete)''',

'Jaisiam Dhoby': '''Dhoby Ghuat Xchange @ SMRT, Panang Lane #(placeholder)
S238826'''
}
NEWORDER_CHOOSE, NEWORDER_INPUT, NEWORDER_NUM, NEWORDER_CUSTOMER, NEWORDER_CUST_INPUT = range(5)

DELETE_ORDER_CHOOSE = range(1)

JOB_ADD_INPUT = range(1)

#================================= Essential Functions =======================================================
def start(update, context):
    text = '''Hi! I am Mindobot, @mindoposbot. I am here to assist you in keeping track of your deliveries.
I will be messaging you from time to time regarding the orders you have accepted, so please update the status of your deliveries through me!'''
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)

def helpcommand(update, context):
    helptext = '''Hi! I am Mindobot, @mindoposbot. I am here to assist you in keeping track of your deliveries.
I will be messaging you from time to time regarding the orders you have accepted, so please update the status of your deliveries through me!

List of commands:
    /orders - Display list of today's orders and current ongoing orders
    '''

    helptext_admin = '''List of admin commands:
    /info - Generate info about bot's stored data
    /neworder - Generate new order
    /start - Start bot
    /stop - Shutdown bot
    '''

    #helptext_owner = 'You created me and you asked for a list of help? Do you have a memory of a goldfish??'

    user = update.message.from_user.id
    context.bot.send_message(chat_id=update.effective_chat.id, text=helptext)
    context.bot.send_message(chat_id=update.effective_chat.id, text=helptext_admin)

def error(update, context):
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = ''.join(tb_list)

    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f'An exception was raised while handling an update\n'
        f'<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}'
        '</pre>\n\n'
        f'<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n'
        f'<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n'
        f'<pre>{html.escape(tb_string)}</pre>'
    )

    while len(message) > 4096:
        msg_out = message[:4092] + '</pre>'
        context.bot.send_message(chat_id=log_chat, text=msg_out, parse_mode='HTML')
        message = '<pre>' + message[4092:]

    context.bot.send_message(chat_id=log_chat, text=message, parse_mode='HTML')

def unknown(update, context):
    text='''Error. Either you are not authorised to use this command or its an unknown command.
Type /help for a list of commands'''
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)

def stopbot(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Shutting down...")

def clear_alldata(update, context):
    context.chat_data.clear()
    context.bot_data.clear()
    context.user_data.clear()

def info(update, context):
    job_list = [f"{job.name} - {job.next_t}" for job in context.job_queue.jobs()]
    job_str = "\n".join(job_list).join(['\n', '\n'])

    message = f'''Update: {update}\n\nBot Data: {context.bot_data}\n\nChat Data: {context.chat_data}\n
Job Data: {job_str}\n\nTime: {datetime.now()}'''

    while len(message) > 4096:
        msg_out = message[:4096]
        context.bot.send_message(chat_id=update.effective_chat.id, text=msg_out)
        message = message[4096:]

    context.bot.send_message(chat_id=update.effective_chat.id, text=message)

def cancel(update, context):
    update.message.reply_text(f'User {update.message.from_user.first_name} canceled command.')

    return ConversationHandler.END

def dict2str(data):
    info = [f'{key} - {value}' for key, value in data.items()]
    return "\n".join(info).join(['\n', '\n'])

def job_save(func, time, data, name):
    with open('job_data.txt', 'a') as writer:
        writer.write(f'{name}-{func}-{time.strftime("%d%m%y %H%M")}-{data}\n')

def job_erase(name):
    with open('job_data.txt', 'r') as reader:
        lines = reader.readlines()
    with open('job_data.txt', 'w') as writer:
        for line in lines:
            line_list = line.split('-')
            if line_list[0] != name:
                writer.write(line)

#=============================== Accept Order ===================================================
def button(update, context):
    query = update.callback_query
    query.answer()
    data = query.data
    user = query.from_user.username
    user_id = query.from_user.id
    text = query.message.text

    if data == 'Accept':
        text_list = text.split()
        orderNo = text_list[2]
        outlet_list = text_list[4:-8]
        outlet = ' '.join([str(i) for i in outlet_list])

        try:
            context.bot.send_message(chat_id=user_id, text=f'You have accepted order #{orderNo} from {outlet}. I will send a message again an hour before pickup.')
        except:
            text = f'''User @{user} have not initiate a chat with bot yet! Accept request denied!\n
To initiate chat with bot, click on the following link (you will be redirected to your browser):
https://t.me/mindoposbot?start=start'''
            context.bot.send_message(chat_id=post_chat, text=text)
            return

        msg = query.edit_message_text(f'@{user} has accepted order #{orderNo} from {outlet}.')
        identifier = '- '.join((outlet, orderNo))
        context.bot_data['msg_id'][identifier][1] = msg.message_id

        order = context.bot_data[outlet][orderNo]
        order['Status'] = 'Accepted'
        order['Accepted by'] = user_id
        time = order['Pickup Time'] - timedelta(hours=1)
        out = [outlet, orderNo, user_id]

        if datetime.now() < time:
            context.job_queue.run_once(delivery, time, context=out, name=f'{outlet} {orderNo}')
            job_save('delivery', time, out, f'{outlet} {orderNo}')
        else:
            context.bot.send_message(chat_id=log_chat, text='Late Accept')
            context.job_queue.run_once(delivery, 5, context=out, name=f'{outlet} {orderNo}')

    elif data == 'Picked up' or data == 'Dropped' or data == 'Back':
        outlet = context.bot_data[user_id]['Outlet']
        orderNo = context.bot_data[user_id]['Order']
        try:
            order = context.bot_data[outlet][orderNo]
        except:
            query.edit_message_text("A fatal error has occured. Please screenshot this conversation and contact Mindopos Admins.")
            return

        if data == 'Picked up':
            context.bot_data[user_id]['Current'] = 0
            context.bot.send_message(chat_id=log_chat, text=f'Order {orderNo} from {outlet} picked up.')
            order['Status'] = 'Ongoing'

        elif data == 'Dropped':
            cur = context.bot_data[user_id]['Current']
            context.bot.send_message(chat_id=log_chat, text=f'Location #{cur} for Order {orderNo} from {outlet} dropped.')

        elif data == 'Back':
            cur = context.bot_data[user_id]['Current']
            if cur <= 1:
                reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Picked up", callback_data='Picked up')]])
                msg = query.edit_message_text(f"Have you picked up order #{orderNo} from {outlet}?", reply_markup = reply_markup)
                identifier = '- '.join((outlet, orderNo))
                context.bot_data['msg_id'][identifier][3] = msg.message_id
                order['Status'] = 'Accepted'
                context.bot.send_message(chat_id=log_chat, text=f'Driver misclicked for Pickup for order #{orderNo} from {outlet}.')
                return

            context.bot.send_message(chat_id=log_chat, text=f'Driver misclicked for drop at Location #{cur-1}, order #{orderNo} from {outlet}.')
            context.bot_data[user_id]['Current'] -= 2

        context.bot_data[user_id]['Current'] += 1
        cur = context.bot_data[user_id]['Current']
        if cur > len(order['Customer'].keys()):
            query.edit_message_text('All orders completed successfully!')
            context.bot.send_message(chat_id=log_chat, text=f'All Orders from Order #{orderNo} from {outlet} completed.')
            order['Status'] = 'Done'
            context.bot_data.pop(user_id)
            return


        text = '\n'.join((f"For Location #{cur}", neworder.dict2str_order(order['Customer'][str(cur)])))
        text += f'''\n
Waze Map: https://waze.com/ul?q={order['Customer'][str(cur)]['Postal']}
Google Map: https://www.google.com/maps/search/Singapore+{order['Customer'][str(cur)]['Postal']}'''
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton('Dropped', callback_data='Dropped')],
            [InlineKeyboardButton('<< Back', callback_data='Back')],
        ])
        query.edit_message_text(text, parse_mode='HTML', reply_markup=reply_markup)

    else:
        query.edit_message_text('Error.')

def delivery(context):
    outlet = context.job.context[0]
    orderNo = context.job.context[1]
    user_id = context.job.context[2]

    data = context.bot_data[outlet][orderNo]
    context.bot_data[user_id] = {'Outlet': outlet, 'Order': orderNo}

    msg1 = neworder.postorder_output(context, user_id, outlet, orderNo)
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Picked up", callback_data='Picked up')]])
    msg2 = context.bot.send_message(chat_id=user_id, text=f"Have you picked up order #{orderNo} from {outlet}?", reply_markup = reply_markup)
    identifier = '- '.join((outlet, orderNo))
    context.bot_data['msg_id'][identifier].append(msg1.message_id)
    context.bot_data['msg_id'][identifier].append(msg2.message_id)

#=============================== Orders Editing ===================================================
def orders(update, context):
    temp_pick = {}
    for outlet, orderNo in context.bot_data.items():
        if outlet not in outlets:
            continue
        for no, info in orderNo.items():
            for key, value in info.items():
                if key == 'Pickup Time':
                    temp = ' Status: '.join((datetime.strftime(value, "%d/%m/%y %a %H%M"), context.bot_data[outlet][no]['Status']))
                    temp_pick[" - ".join((outlet, '<b>'+no+'</b>'))] = temp

    if len(temp_pick.keys()) == 0:
        text = f'No orders for {datetime.strftime(datetime.now(), "%d/%m/%y")}'
    else:
        temp_pick = dict(sorted(temp_pick.items(), key=lambda item: item[1]))
        text = f'<u>List of orders sorted by pickup timing:</u>{dict2str(temp_pick)}'

    update.message.reply_text(text, parse_mode='HTML')

def clear_botdata(update, context):
    context.bot_data.clear()
    for i in outlets:
        context.bot_data[i] = {}
    update.message.reply_text('Bot data has been cleared!')

def clear_chatdata(update, context):
    context.chat_data.clear()
    update.message.reply_text('Chat data has been cleared!')


def delete_order(update, context):
    temp_list = []
    for outlet in context.bot_data.keys():
        if outlet in outlets:
            for orderNo in context.bot_data[outlet].keys():
                if context.bot_data[outlet][orderNo]['Status'] in ['Accepted', 'Posted']:
                    output = "-".join((outlet, orderNo))
                    temp_list.append([InlineKeyboardButton(output.replace('-', ' '), callback_data=output)])

    if len(temp_list) == 0:
        update.message.reply_text('There are no posted or accepted orders to be deleted.')
        return ConversationHandler.END

    else:
        text = '''Select orders to delete.\n\nOnce order is deleted, it cannot be undone! If driver had accepted the order, they will be updated about cancellation of the order.'''
        update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(temp_list))
        return DELETE_ORDER_CHOOSE

def delete_order_choose(update, context):
    query = update.callback_query
    query.answer()
    data = query.data
    temp_list = data.split('-')
    outlet = temp_list[0]
    orderNo = temp_list[1]

    query.edit_message_text('Deleting order...')
    identifier = '- '.join((outlet, orderNo))
    msg_id = context.bot_data['msg_id'][identifier]

    if context.bot_data[outlet][orderNo]['Status'] == 'Accepted':
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"{outlet} order #{orderNo} is accepted. User will be inform of its deletion.")
        user_id = context.bot_data[outlet][orderNo]['Accepted by']
        text = f'''Order #{orderNo} from {outlet} has been deleted. You no longer have to go pick up this order\n
I am sorry for the inconvenience caused. For further enquries, please contact Mindopos Admins.'''

        context.bot.send_message(chat_id=user_id, text=text)
        if len(msg_id) > 2:
            context.bot.delete_message(user_id, msg_id[2])
            context.bot.delete_message(user_id, msg_id[3])

        job_tuple = context.job_queue.get_jobs_by_name(f'{outlet} {orderNo}')
        if len(job_tuple):
            job_tuple[0].schedule_removal()

    del context.bot_data[outlet][orderNo]
    context.bot.delete_message(post_chat, msg_id[0])
    context.bot.delete_message(post_chat, msg_id[1])

    del context.bot_data['msg_id'][identifier]
    context.bot.send_message(chat_id=update.effective_chat.id, text='Order successfully deleted')
    return ConversationHandler.END

def job_add(update, context):
    update.message.reply_text('Enter job data to be added: ddmmyyHHMM outlet orderNo user_id:')
    return JOB_ADD_INPUT

def job_addInput(update, context):
    text_list = update.message.text.split('-')
    print(text_list)

    time = datetime.strptime(text_list[0], '%d%m%y%H%M')
    outlet = text_list[1]
    orderNo = text_list[2]
    user_id = text_list[3]
    out = [outlet, orderNo, user_id]

    context.job_queue.run_once(delivery, time, context=out, name=f'{outlet} {orderNo}')
    job_save('delivery', time, out, f'{outlet} {orderNo}')
    return ConversationHandler.END

#=============================== Main Program ===================================================
def main():
    bot = telegram.Bot(token)
    defaults = telegram.ext.Defaults(tzinfo=pytz.timezone('Asia/Singapore'))
    persistence = PicklePersistence(filename='conversationbot', store_chat_data=True)
    updater = Updater(token=token, use_context=True, persistence=persistence, defaults=defaults)
    dp = updater.dispatcher
    j = updater.job_queue

    #Commands to recognize
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('orders', orders))
    dp.add_handler(CommandHandler('help', helpcommand))
    dp.add_handler(CommandHandler('info', info, filters=Filters.user(admins)))
    dp.add_handler(CommandHandler('clear_alldata', clear_alldata, filters=Filters.user(owner)))
    dp.add_handler(CommandHandler('clear_botdata', clear_botdata, filters=Filters.user(owner)))
    dp.add_handler(CommandHandler('clear_chatdata', clear_chatdata, filters=Filters.user(owner)))
    #dp.add_handler(CommandHandler('stop', stopbot, filters=Filters.user(owner)))

    #Conversation Handler
    neworder_convhandler = ConversationHandler(
        entry_points=[CommandHandler('neworder', neworder, filters=Filters.user(admins) & Filters.chat({log_chat, owner}))],
        states={
            NEWORDER_CHOOSE: [
                CallbackQueryHandler(neworder.choose)
            ],
            NEWORDER_INPUT: [
                MessageHandler(Filters.text & ~Filters.command, neworder.inputField),
                CallbackQueryHandler(neworder.inputButton)
            ],
            NEWORDER_NUM: [
                CallbackQueryHandler(neworder.number)
            ],
            NEWORDER_CUSTOMER: [
                CallbackQueryHandler(neworder.cust)
            ],
            NEWORDER_CUST_INPUT: [
                MessageHandler(Filters.text & ~Filters.command, neworder.custInput)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        conversation_timeout=900,
        per_user=False
    )

    delete_order_convhandler = ConversationHandler(
        entry_points=[CommandHandler('delete_order', delete_order, filters=Filters.user(admins) & Filters.chat({log_chat, owner}))],
        states={
            DELETE_ORDER_CHOOSE:[
                CallbackQueryHandler(delete_order_choose)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        conversation_timeout=60,
        per_user=False
    )

    job_add_convhandler = ConversationHandler(
        entry_points=[CommandHandler('job_add', job_add, filters=Filters.user(owner))],
        states={
            JOB_ADD_INPUT:[
                MessageHandler(Filters.text & ~Filters.command, job_addInput)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        conversation_timeout=60
    )
    dp.add_handler(neworder_convhandler)
    dp.add_handler(delete_order_convhandler)
    dp.add_handler(job_add_convhandler)

    dp.add_handler(MessageHandler(Filters.command, unknown))
    dp.add_error_handler(error)

    #Button Handler
    dp.add_handler(CallbackQueryHandler(button))

    #Load Saved Data
    with open('job_data.txt', 'w+') as writer:
        pass
    with open('job_data.txt', 'r') as reader:
        lines = reader.readlines()
    with open('job_data.txt', 'w') as writer:
        for line in lines:
            line_list = line.split('-')
            time = datetime.strptime(line_list[2], '%d%m%y %H%M')
            if datetime.now() < time:
                writer.write(line)
                if line_list[1] == 'delivery':
                    temp = line_list[3].strip("[]").replace("'", '').split(', ')
                    temp[2] = int(temp[2])
                    j.run_once(callback=delivery, when=time, context=temp, name=line_list[0])
    print('Job Data loaded')

    #Run the bot
    print(globals())
    print('Telegram Bot Ready.')
    logger.info('Telegram bot ready.')
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
