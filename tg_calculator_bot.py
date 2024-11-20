import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, ConversationHandler, filters
)
from states import BotStates
from calculator import get_credit_details, get_monthly_payment
from utils import format_payment_for_message, format_payment_table, is_valid_number

# Состояния
STATE = BotStates

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветствие и первый вопрос."""
    context.user_data.clear()  # Очищаем данные пользователя
    user = update.message.from_user
    context.user_data['user_data'] = user
    print(user)
    await update.message.reply_text("Добро пожаловать! Давайте рассчитаем ваш кредит.")
    await update.message.reply_text("Введите сумму кредита (например: 100000):")
    return STATE.ASK_AMOUNT

async def ask_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка суммы кредита."""
    text = update.message.text
    if not text.isdigit():
        await update.message.reply_text("Пожалуйста, введите корректную сумму (например: 100000).")
        return STATE.ASK_AMOUNT

    # Сохраняем сумму в context.user_data
    context.user_data['amount'] = int(text)
    await update.message.reply_text("Введите срок кредита в месяцах (например: 12):")
    return STATE.ASK_TERM

async def ask_term(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка срока кредита."""
    text = update.message.text
    if not text.isdigit():
        await update.message.reply_text("Пожалуйста, введите корректный срок (например: 12).")
        return STATE.ASK_TERM

    # Сохраняем срок в context.user_data
    context.user_data['term'] = int(text)
    await update.message.reply_text("Введите годовую процентную ставку (например: 5.5):")
    return STATE.ASK_RATE

async def ask_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка процентной ставки."""
    text = update.message.text
    if not is_valid_number(text):
        await update.message.reply_text("Пожалуйста, введите корректную ставку (например: 5.5).")
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
        [InlineKeyboardButton("Расчитать новый кредит", callback_data="restart")],
        [InlineKeyboardButton("Получить список платежей", callback_data="show_payments")],
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

async def handle_show_payments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопки 'Получить список платежей'."""
    query = update.callback_query
    payments = context.user_data['payments']
    payments_table = format_payment_table(payments)
    print(payments_table)

    # Экран с таблицей платежей и кнопками
    keyboard = [
        [InlineKeyboardButton("Расчитать новый кредит", callback_data="restart")],
        [InlineKeyboardButton("Вернуться к результатам", callback_data="show_results")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Эксперименты с экранированием символов для MarkdownV2
    payments_table = payments_table.replace("_", "\\_").replace("*", "\\*").replace("`", "\\`")
    
    # Отправляем отформатированное сообщение
    await query.edit_message_text(f"```{payments_table}```", parse_mode="MarkdownV2", reply_markup=reply_markup)
    # await query.edit_message_text(payments_table, parse_mode="Markdown", reply_markup=reply_markup)
    
    
    return STATE.SHOW_RESULT

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
        [InlineKeyboardButton("Расчитать новый кредит", callback_data="restart")],
        [InlineKeyboardButton("Получить список платежей", callback_data="show_payments")],
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
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            STATE.ASK_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_amount)],
            STATE.ASK_TERM: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_term)],
            STATE.ASK_RATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_rate)],
            STATE.SHOW_RESULT: [
                CallbackQueryHandler(handle_show_payments, pattern="show_payments"),
                CallbackQueryHandler(handle_restart, pattern="restart"),
                CallbackQueryHandler(handle_show_results, pattern="show_results"),  # Новый обработчик
            ],
        },
        fallbacks=[CommandHandler("start", fallback)],
    )
    
    app.add_handler(conv_handler)
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
