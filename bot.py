import os
from datetime import date
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext


# Настройки для подключения к Google Sheets
scope = ["https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
gc = gspread.authorize(creds)
sheet = gc.open("Название_вашей_таблицы").sheet1

# Функция для получения доступных слотов
def get_available_slots():
    rows = sheet.get_all_values()
    available_slots = []
    
    for row in rows[1:]:
        if len(row) >= 4 and row[3].lower() == 'true':
            available_slots.append(f"{row[0]} {row[1]} - {row[2]}")
            
    return available_slots

# Команда /start
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Добро пожаловать в автошколу! Чтобы забронировать занятие, нажмите кнопку ниже.",
        reply_markup=ReplyKeyboardMarkup([['Забронировать']], resize_keyboard=True),
    )

# Обработка команды 'Забронировать'
def book(update: Update, context: CallbackContext):
    slots = get_available_slots()
    if not slots:
        update.message.reply_text("К сожалению, все слоты заняты. Попробуйте позже.")
        return
        
    keyboard = [[slot] for slot in slots]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    update.message.reply_text("Выберите доступный слот:", reply_markup=reply_markup)

# Получение выбранного слота
def select_slot(update: Update, context: CallbackContext):
    selected_slot = update.message.text
    context.user_data['selected_slot'] = selected_slot
    update.message.reply_text(
        f"Вам подходит этот слот? {selected_slot}",
        reply_markup=ReplyKeyboardMarkup([['Да'], ['Нет']], resize_keyboard=True),
    )

# Подтверждение бронирования
def confirm_booking(update: Update, context: CallbackContext):
    answer = update.message.text
    if answer.lower() != 'да':
        update.message.reply_text("Понял, отменяем бронирование.")
        return
    
    update.message.reply_text("Введите ваше полное имя:")

# Получение полного имени
def get_full_name(update: Update, context: CallbackContext):
    full_name = update.message.text
    context.user_data['full_name'] = full_name
    update.message.reply_text("Теперь введите ваш контактный телефон:")

# Получение номера телефона
def get_phone_number(update: Update, context: CallbackContext):
    phone_number = update.message.text
    context.user_data['phone_number'] = phone_number
    
    # Запись данных в Google Sheet
    selected_slot = context.user_data['selected_slot']
    full_name = context.user_data['full_name']
    phone_number = context.user_data['phone_number']
    
    rows = sheet.get_all_values()
    for i, row in enumerate(rows[1:], start=2):
        if f"{row[0]} {row[1]}" in selected_slot:
            sheet.update_cell(i, 4, 'false')
            break
    
    update.message.reply_text(
        f"Бронь успешно создана!\nИмя: {full_name}\nТелефон: {phone_number}\nДата и время: {selected_slot}"
    )

# Основной обработчик сообщений
def handle_message(update: Update, context: CallbackContext):
    text = update.message.text
    if text == 'Забронировать':
        return book(update, context)
    elif text == 'Да':
        return confirm_booking(update, context)
    else:
        update.message.reply_text("Не понимаю вас. Пожалуйста, выберите одну из предложенных кнопок.")

# Главная функция запуска бота
def main():
    updater = Updater(os.environ["TELEGRAM_TOKEN"], use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.regex('^Забронировать$'), book))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
