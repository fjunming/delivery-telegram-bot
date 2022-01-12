def dict2str_order(data):
    var = []
    for key, value in data.items():
        if key == 'Customer':
            continue
        if value == None:
            value = f'<u>{value}</u>'
        elif key == 'Contact':
            pass
        else:
            value = f'<b>{value}</b>'

        var.append(f'{key}: {value}')

    return "\n".join(var)

def check_missCustDetails(data):
    for key, value in data.items():
        if key == 'Remarks':
            continue
        if value == None:
            return True
    return False


def printOutput(update, context):
    neworder_keyboard = [
        [InlineKeyboardButton('Outlet', callback_data='Outlet'),
         InlineKeyboardButton('Pickup Date', callback_data='Pickup Date')],
        [InlineKeyboardButton('Pickup Time', callback_data='Pickup Time'),
         InlineKeyboardButton('Order Number', callback_data='Order Number')],
        [InlineKeyboardButton('Number of Orders', callback_data='Number of Orders'),
         InlineKeyboardButton("Price", callback_data="Price")],
        [InlineKeyboardButton("Customer's Details", callback_data="Customer's Details")],
        [InlineKeyboardButton("Confirm", callback_data="Confirm")],
        [InlineKeyboardButton('-Cancel-', callback_data='cancel')]
    ]

    var = context.chat_data['Customer']
    var_str = ''
    if var != None:
        for i in var:
            var_str = '\n\n'.join((var_str, f'Customer {i}'))
            var_str = '\n'.join((var_str, dict2str_order(var[i])))

    text = f'Order details:\n\n{dict2str_order(context.chat_data)}{var_str}\n\nSelect category:'

    if update.callback_query:
        update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(neworder_keyboard),
                                                parse_mode='HTML')
    else:
        update.message.reply_text(text=text, reply_markup=InlineKeyboardMarkup(neworder_keyboard), parse_mode='HTML')


def custPrint(update, context):
    neworder_keyboard2 = [
        [InlineKeyboardButton('Name', callback_data='Name'), InlineKeyboardButton('Contact', callback_data='Contact')],
        [InlineKeyboardButton('Deliver by', callback_data='Deliver by'),
         InlineKeyboardButton('Address', callback_data='Address')],
        [InlineKeyboardButton('Postal', callback_data='Postal'),
         InlineKeyboardButton("Remarks", callback_data="Remarks")],
        [InlineKeyboardButton("<< Back to Main Menu", callback_data="Back")]
    ]

    cust = context.chat_data['Customer']['Current']
    var = context.chat_data['Customer'][cust]

    text = f'Customer {cust} details:\n{dict2str_order(var)}\nSelect category:'

    if update.callback_query:
        update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(neworder_keyboard2),
                                                parse_mode='HTML')
    else:
        update.message.reply_text(text=text, reply_markup=InlineKeyboardMarkup(neworder_keyboard2), parse_mode='HTML')


def initial(update, context):
    update.message.reply_text('Creating new order...')
    context.chat_data.clear()
    neworder_list = ['Outlet', 'Pickup Date', 'Pickup Time', 'Order Number', 'Number of Orders', 'Price',
                     'Customer']

    for i in neworder_list:
        context.chat_data[i] = None
    context.bot.send_message(chat_id=update.effective_chat.id, text="Pickup Outlet",
                             reply_markup=InlineKeyboardMarkup(outlets_keyboard))

    return NEWORDER_INPUT


def inputButton(update, context):
    query = update.callback_query
    query.answer()
    data = query.data

    if data in outlets:
        context.chat_data['Outlet'] = data
    else:
        context.chat_data['Pickup Date'] = data

    printOutput(update, context)
    return NEWORDER_CHOOSE


def choose(update, context):
    query = update.callback_query
    query.answer()
    data = query.data

    if data == 'Outlet':
        query.edit_message_text('Pickup Outlet', reply_markup=InlineKeyboardMarkup(outlets_keyboard))
        return NEWORDER_INPUT


    elif data == 'Pickup Date':
        date_keyboard = []

        for i in range(5):
            d = (datetime.now() + timedelta(days=i)).date().strftime("%d %B %y %a")
            date_keyboard.append([InlineKeyboardButton(d, callback_data=d)])

        query.edit_message_text('Select Date', reply_markup=InlineKeyboardMarkup(date_keyboard))
        return NEWORDER_INPUT

    elif data == 'Price':
        context.chat_data['choose'] = data
        query.edit_message_text('Enter total earnings for driver for this order number:')

        return NEWORDER_INPUT

    elif data == "Customer's Details":
        num = context.chat_data['Number of Orders']
        if num == None:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="Invalid Category! Please input number of orders first!")
            return

        num = int(num)
        num_keyboard = []
        for i in range(num):
            num_keyboard.append([InlineKeyboardButton('#' + str(i + 1), callback_data=str(i + 1))])

        query.edit_message_text(f'Select which of the following {num} customers to edit',
                                reply_markup=InlineKeyboardMarkup(num_keyboard))

        return NEWORDER_NUM

    elif data == 'Confirm':
        for key, value in context.chat_data.items():
            if value == None:
                context.bot.send_message(chat_id=update.effective_chat.id,
                                         text=f"Order details not completed! Please check {key} and re-select!")
                return

        num = int(context.chat_data['Number of Orders'])
        if num != len(context.chat_data['Customer'].keys()):
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=f"Missing customer details! Please check and re-select!")
            return
        else:
            for i in range(1, num + 1):
                cust = context.chat_data['Customer'][str(i)]
                if check_missCustDetails(cust):
                    context.bot.send_message(chat_id=update.effective_chat.id,
                                             text=f"Missing customer details! Please check and re-select!")
                    return

            date_time = ' '.join((context.chat_data['Pickup Date'], context.chat_data['Pickup Time']))
            date_time = datetime.strptime(date_time, "%d %B %y %a %H%M")
            outlet = context.chat_data['Outlet']
            orderNo = context.chat_data['Order Number']

            if outlet not in context.bot_data.keys():
                context.bot_data[outlet] = {}

            if orderNo in context.bot_data[outlet].keys():
                context.bot.send_message(chat_id=update.effective_chat.id, text=f"Duplicate Order Number! Please check")
                return

            query.edit_message_text(f"Order will now be posted")
            context.bot_data[outlet][orderNo] = {}
            order = context.bot_data[outlet][orderNo]
            order['Pickup Time'] = date_time
            order['Price'] = context.chat_data['Price']
            order['Customer'] = {}
            num = int(context.chat_data['Number of Orders'])

            for i in range(1, num + 1):
                order['Customer'][str(i)] = {}
                order['Customer'][str(i)] = context.chat_data['Customer'][str(i)]

            msg1 = postorder_output(context, post_chat, outlet, orderNo)

            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Accept", callback_data='Accept')]])
            msg2 = context.bot.send_message(chat_id=post_chat,
                                            text=f'Accept order {orderNo} from {outlet} ?\n(You may be redirected to telegram webpage)',
                                            reply_markup=reply_markup)

            if 'msg_id' not in context.bot_data.keys():
                context.bot_data['msg_id'] = {}

            identifier = '- '.join((outlet, orderNo))
            context.bot_data['msg_id'][identifier] = [msg1.message_id, msg2.message_id]
            order['Status'] = 'Posted'
            context.bot.send_message(chat_id=update.effective_chat.id, text='Order posted successfully')
            # context.chat_data.clear() IN TESTING MODE
            return ConversationHandler.END

    elif data == 'cancel':
        query.edit_message_text(f'{query.from_user.first_name} cancelled neworder command.')
        return ConversationHandler.END

    else:
        context.chat_data['choose'] = data
        query.edit_message_text(f'Enter {data}:')

    return NEWORDER_INPUT


def inputField(update, context):
    text = update.message.text
    cat = context.chat_data['choose']

    # Checks
    if cat == 'Number of Orders':
        if (not text.isnumeric()) or (int(text) < 0):
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="Invalid Input, must be positive number! Please re-enter:")
            return

        if (context.chat_data['Customer'] != None) and (int(text) < len(context.chat_data['Customer'].keys())):
            temp_list = []
            for i in context.chat_data['Customer'].keys():
                if int(i) > int(text):
                    break
                temp_dict = {}
                temp_dict[i] = context.chat_data['Customer'][i]
                temp_list.append(temp_dict)

            context.chat_data['Customer'].clear()
            for i in range(1, int(text) + 1):
                context.chat_data['Customer'][i] = temp_list[i - 1]

    elif (cat == 'Pickup Time') and (not text.isnumeric() or len(text) != 4 or int(text) < 0 or int(text) > 2359):
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Invalid Input, time must be in 24hr format (0000 - 2359)! Please re-enter:")
        return

    context.chat_data.pop('choose')
    context.chat_data[cat] = text
    printOutput(update, context)
    return NEWORDER_CHOOSE


def number(update, context):
    query = update.callback_query
    query.answer()
    data = query.data
    customer_details = ['Name', 'Contact', 'Deliver by', 'Address', 'Postal', 'Remarks']

    if context.chat_data['Customer'] == None:
        context.chat_data['Customer'] = {}

    if data not in context.chat_data['Customer']:
        context.chat_data['Customer'][data] = {}
        for i in customer_details:
            context.chat_data['Customer'][data][i] = None

    context.chat_data['Customer']['Current'] = data
    custPrint(update, context)

    return NEWORDER_CUSTOMER


def cust(update, context):
    query = update.callback_query
    query.answer()
    data = query.data

    if data == 'Back':
        context.chat_data['Customer'].pop('Current')
        printOutput(update, context)
        return NEWORDER_CHOOSE

    num = context.chat_data['Customer']['Current']
    context.chat_data['choose'] = data
    query.edit_message_text(f"Enter Customer #{num}'s {data}:")

    return NEWORDER_CUST_INPUT


def custInput(update, context):
    text = update.message.text
    cat = context.chat_data['choose']
    num = context.chat_data['Customer']['Current']

    # Checks
    if (cat == 'Contact') and (not text.isnumeric() or len(text.replace(' ', '')) != 8):
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Invalid Input, must be a proper Singapore 8 digit phone number! Please re-enter:")
        return

    elif (cat == 'Postal') and (not text.isnumeric() or len(text) != 6):
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Invalid Input, must be a proper 6 digit numerical postal code! Please re-enter:")
        return

    context.chat_data.pop('choose')
    context.chat_data['Customer'][num][cat] = text
    custPrint(update, context)

    return NEWORDER_CUSTOMER


def postorder_output(context, chat, outlet, orderNo):
    order = context.bot_data[outlet][orderNo]
    output_text = f'''Order Number: <b>{orderNo}</b>
Pickup Location:
    <b>{outletinfo[outlet]}</b>

Pickup Time: <b>{datetime.strftime(order['Pickup Time'], '%d %b %Y (%a) at %H%Mhrs')}</b>
Price: <b><u>{order['Price']}</u></b>\n\n'''

    for i in range(len(order['Customer'].keys())):
        output_loop = '\n'.join((f"For Location {i + 1}", dict2str_order(order['Customer'][str(i + 1)])))
        output_text += (output_loop + '\n\n')

    return context.bot.send_message(chat_id=chat, text=output_text, parse_mode='HTML')