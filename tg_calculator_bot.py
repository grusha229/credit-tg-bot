import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, ConversationHandler, filters
)
from states import BotStates
from calculator import get_credit_details, get_monthly_payment
from utils import format_payment_for_message, is_valid_number

# Состояния
STATE = BotStates

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветствие и первый вопрос."""
    context.user_data.clear()  # Очищаем данные пользователя
    user = update.message.from_user
    context.user_data['user_data'] = user
    print(user)
    await update.message.reply_text("Добро пожаловать! Это бот для расчета кредита. Давайте посчитаем ваш кредит.")
    await update.message.reply_text("Введите сумму кредита (например: 100000):")
    return STATE.ASK_AMOUNT

async def ask_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка суммы кредита."""
    text = update.message.text
    if (not text.isdigit()) or int(text) > 1_000_000_000 or int(text) < 1:
        await update.message.reply_text("Пожалуйста, введите корректную сумму (например: 100000). От 1 рубля до 1 миллиарда рублей")
        return STATE.ASK_AMOUNT

    # Сохраняем сумму в context.user_data
    context.user_data['amount'] = int(text)
    await update.message.reply_text("Введите срок кредита в месяцах (например: 12):")
    return STATE.ASK_TERM

async def ask_term(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка срока кредита."""
    text = update.message.text
    if (not text.isdigit()) or int(text) > 12*30 or int(text) < 1:
        await update.message.reply_text("Пожалуйста, введите корректный срок (например: 12). От 1 месяца до 30 лет")
        return STATE.ASK_TERM

    # Сохраняем срок в context.user_data
    context.user_data['term'] = int(text)
    await update.message.reply_text("Введите годовую процентную ставку (например: 5.5):")
    return STATE.ASK_RATE

async def ask_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка процентной ставки."""
    text = update.message.text
    if not is_valid_number(text) or float(text) > 100 or float(text) < 1:
        await update.message.reply_text("Пожалуйста, введите корректную ставку (например: 5.5). Ставка должна быть в диапазоне от 1 до 100 %")
        return STATE.ASK_RATE

    # Сохраняем ставку в context.user_data
    context.user_data['rate'] = float(text)

    # Получаем введенные данные
    amount = context.user_data['amount']
    term = context.user_data['term']
    rate = context.user_data['rate']

    # Вычисляем результат
    monthly_payment = get_monthly_payment(amount, rate, term)
    total_payment, overpayment, payments = get_credit_details(amount, rate, term)

    context.user_data['monthly_payment'] = monthly_payment
    context.user_data['total_payment'] = total_payment
    context.user_data['overpayment'] = overpayment
    context.user_data['payments'] = payments

    # Показываем кнопки для дальнейших действий
    keyboard = [
        [],
        [
            InlineKeyboardButton("Расчитать новый кредит", callback_data="restart"),
            InlineKeyboardButton("Получить список платежей", callback_data="show_payments")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Выводим результат
    await update.message.reply_text(
        f"Сумма кредита: *{amount:,.2f} рублей.* \n"
        f"Срок кредита: *{term} месяцев.* \n"
        f"Процентная ставка: *{rate:.2f} %.* \n"
        f"\n"
        f"Ежемесячный платеж составит: `{monthly_payment:,.2f}` рублей. \n"
        f"Переплата: `{overpayment:,.2f}` рублей. \n"
        f"Общая сумма займа: `{total_payment:,.2f}` рублей. \n",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

    return STATE.SHOW_RESULT

async def handle_restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопки 'Начать заново'."""
    query = update.callback_query
    await query.answer()

    # Отправляем сообщение о возврате на стартовый экран
    await query.edit_message_text("Вы вернулись на стартовый экран. Начнем заново!")
    
    # Очищаем данные пользователя перед началом нового расчета
    context.user_data.clear()
    
    # Возвращаем пользователя на стадию с вопросом о сумме
    await query.message.reply_text("Введите сумму кредита (например: 100000):")
    return STATE.ASK_AMOUNT

def paginate_list(data, page_size):
    """Разделяет список на страницы заданного размера."""
    return [data[i:i + page_size] for i in range(0, len(data), page_size)]

async def handle_show_payments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопки 'Получить список платежей'."""
    query = update.callback_query
    payments = context.user_data['payments']
    page_size = 6  # Показываем 6 элементов на странице
    current_page = context.user_data.get('current_page', 0)  # Текущая страница по умолчанию 0
    
    # Разделяем платежи на страницы
    pages = paginate_list(payments, page_size)
    
    # Получаем платежи для текущей страницы
    current_payments = pages[current_page]
    
    # Форматируем платежи для сообщения
    payments_table = format_payment_for_message(current_payments)

    # Создание кнопок навигации
    keyboard = [
        [],
        [
            InlineKeyboardButton("Расчитать новый кредит", callback_data="restart"),
            InlineKeyboardButton("Вернуться к результатам", callback_data="show_results")
        ]
    ]
    
    # Кнопка "Предыдущая страница"
    if current_page > 0:
        keyboard[0].append(InlineKeyboardButton(f"⬅️ Страница {current_page} / {len(pages) }", callback_data="prev_page"))
    
    # Кнопка "Следующая страница"
    if current_page < len(pages) - 1:
        keyboard[0].append(InlineKeyboardButton(f"Страница {current_page + 2} / {len(pages) } ➡️", callback_data="next_page"))

    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Эксперименты с экранированием символов для MarkdownV2
    payments_table = payments_table.replace("_", "\\_").replace("*", "\\*").replace("`", "\\`")
    
    # Отправляем отформатированное сообщение
    await query.edit_message_text(f"```{payments_table}Cтраница {current_page + 1} из {len(pages)}```", parse_mode="MarkdownV2", reply_markup=reply_markup)
    
    return STATE.SHOW_RESULT

async def handle_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка навигации по страницам платежей."""
    query = update.callback_query
    data = query.data  # Сохраняем данные, переданные через колбэк
    
    # Получаем текущую страницу из user_data
    current_page = context.user_data.get('current_page', 0)
    payments = context.user_data['payments']
    page_size = 5  # Размер страницы
    
    # Разделяем платежи на страницы
    pages = paginate_list(payments, page_size)
    
    # Определяем, какая кнопка была нажата
    if data == "next_page":
        # Переход к следующей странице
        if current_page < len(pages) - 1:
            current_page += 1
    elif data == "prev_page":
        # Переход к предыдущей странице
        if current_page > 0:
            current_page -= 1
    
    # Сохраняем текущую страницу в user_data
    context.user_data['current_page'] = current_page
    
    # Получаем платежи для текущей страницы
    current_payments = pages[current_page]
    
    # Форматируем платежи для сообщения
    payments_table = format_payment_for_message(current_payments)

    # Создание кнопок навигации
    keyboard = [
        [],
        [
            InlineKeyboardButton("Расчитать новый кредит", callback_data="restart"),
            InlineKeyboardButton("Вернуться к результатам", callback_data="show_results")
        ]
    ]
    
    # Кнопка "Предыдущая страница"
    if current_page > 0:
        keyboard[0].append(InlineKeyboardButton(f"⬅️ Страница {current_page} / {len(pages)}", callback_data="prev_page"))
    
    # Кнопка "Следующая страница"
    if current_page < len(pages) - 1:
        keyboard[0].append(InlineKeyboardButton(f"Страница {current_page + 2} / {len(pages)} ➡️", callback_data="next_page"))
    
    # Добавляем дополнительные кнопки    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Эксперименты с экранированием символов для MarkdownV2
    payments_table = payments_table.replace("_", "\\_").replace("*", "\\*").replace("`", "\\`")
    
    # Отправляем отформатированное сообщение
    await query.edit_message_text(f"```{payments_table}Cтраница {current_page + 1} из {len(pages)}```", parse_mode="MarkdownV2", reply_markup=reply_markup)


async def handle_show_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопки 'Вернуться к результатам'."""
    query = update.callback_query
    await query.answer()

    # Получаем сохраненные данные
    amount = context.user_data['amount']
    term = context.user_data['term']
    rate = context.user_data['rate']
    monthly_payment = context.user_data['monthly_payment']
    total_payment = context.user_data['total_payment']
    overpayment = context.user_data['overpayment']

    # Показываем кнопку для перехода к списку платежей
    keyboard = [
        [],
        [
            InlineKeyboardButton("Расчитать новый кредит", callback_data="restart"),
            InlineKeyboardButton("Получить список платежей", callback_data="show_payments")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Повторно показываем результаты
    await query.edit_message_text(
        f"Сумма кредита: *{amount:,.2f} рублей.* \n"
        f"Срок кредита: *{term} месяцев.* \n"
        f"Процентная ставка: *{rate:.2f} %.* \n"
        f"\n"
        f"Ежемесячный платеж составит: `{monthly_payment:,.2f}` рублей. \n"
        f"Переплата: `{overpayment:,.2f}` рублей. \n"
        f"Общая сумма займа: `{total_payment:,.2f}` рублей. \n",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

    return STATE.SHOW_RESULT

async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка команды для возвращения на предыдущий шаг."""
    await update.message.reply_text("Напишите /start для начала заново.")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token('8063856327:AAHhWSllLaxQbx31ATCFnCEHVYaMspwDoQQ').build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            STATE.ASK_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_amount)],
            STATE.ASK_TERM: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_term)],
            STATE.ASK_RATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_rate)],
            STATE.SHOW_RESULT: [
                CallbackQueryHandler(handle_show_payments, pattern="show_payments"),
                CallbackQueryHandler(handle_restart, pattern="restart"),
                CallbackQueryHandler(handle_show_results, pattern="show_results"),
                CallbackQueryHandler(handle_navigation, pattern="next_page"),
                CallbackQueryHandler(handle_navigation, pattern="prev_page"),
            ],
        },
        fallbacks=[CommandHandler("start", fallback)],
    )
    
    app.add_handler(conv_handler)
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
