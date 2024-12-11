def is_valid_number(input_text):
    try:
        float(input_text)
        return True
    except ValueError:
        return False


def format_payment_for_message(payments):
    """Форматируем список платежей для отправки в сообщение."""
    # Заголовок таблицы
    table = "Расчёт Список платежей:\n\n"

    # Заполняем строки таблицы данными
    for payment in payments:
        table += f"{payment['id']}) {payment['month']: <12}\n" \
                 f"Платёж: {'': <11}{payment['payment']: >12,.2f} руб.\n" \
                 f"Проценты: {'': <9}{payment['interest_payment']: >12,.2f} руб.\n" \
                 f"Основной долг: {'': <4}{payment['principal_payment']: >12,.2f} руб.\n" \
                 f"Остаток долга: {'': <4}{payment['remaining_balance']: >12,.2f} руб.\n\n"

    return table.replace(",", " ")  # Меняем запятые на пробелы для русской локали