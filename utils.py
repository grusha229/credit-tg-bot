def is_valid_number(input_text):
    try:
        float(input_text)
        return True
    except ValueError:
        return False


def format_payment_table(payments):
    # Заголовок таблицы
    table = " Месяц |   Платеж    |   Проценты  | Основной долг | Остаток долга\n"
    table += "-" * 66 + "\n"
    
    # Заполняем строки таблицы данными
    for payment in payments:
        table += f"{payment['month']:>6} | " \
                 f"{payment['payment']:>11,.2f} | " \
                 f"{payment['interest_payment']:>11,.2f} | " \
                 f"{payment['principal_payment']:>13,.2f} | " \
                 f"{payment['remaining_balance']:>13,.2f}\n"
    
    return table.replace(",", " ")  # Меняем запятые на пробелы для русской локали

def format_payment_for_message(payments):
    """Форматируем список платежей для отправки в сообщение."""
    # Заголовок таблицы
    table = "Список платежей: \n"

    # Заполняем строки таблицы данными
    for payment in payments:
        table += f"{payment['month']}) *Платёж:* {payment['payment']:,.2f} руб." \
                 f" *Проценты:* `{payment['interest_payment']:,.2f}` руб." \
                 f" *Основной долг:* `{payment['principal_payment']:,.2f}` руб." \
                 f" *Остаток долга:* `{payment['remaining_balance']:,.2f}` руб.\n\n"

    return table.replace(",", " ")  # Меняем запятые на пробелы для русской локали