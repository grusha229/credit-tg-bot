from datetime import datetime
from dateutil.relativedelta import relativedelta

def get_monthly_payment(amount, annual_rate, months):
    # Переводим годовую процентную ставку в месячную
    monthly_rate = annual_rate / 12 / 100
    return amount * monthly_rate * (1 + monthly_rate) ** months / ((1 + monthly_rate) ** months - 1)

# amount - сумма кредита 
# annual_rate - процентная ставка
# month - кол-во месяцев
# monthly_rate - годовая процентная ставка в пересчёте на месяцы (разделили на 12)
def get_credit_details(amount, annual_rate, months):
    # Переводим годовую процентную ставку в месячную
    monthly_rate = annual_rate / 12 / 100
    total_payment = 0
    payments = []
    remaining_balance = amount

    # Рассчитаем ежемесячный платёж по сложному проценту
    monthly_payment = get_monthly_payment(amount, annual_rate, months)
    current_date = datetime.today()

    # Итерация по каждому месяцу
    for month in range(1, months + 1):
        # Проценты за месяц (проценты начисляются на остаток долга с учётом сложного процента)
        interest_payment = remaining_balance * monthly_rate
        # Платеж, который будет направлен на погашение основного долга
        principal_payment = monthly_payment - interest_payment
        # Обновляем остаток долга
        remaining_balance = remaining_balance + interest_payment - monthly_payment

        # Сохраняем данные для отчёта
        payments.append({
            'id': month,
            'month': current_date.strftime('%d.%m.%Y'),
            'payment': round(monthly_payment, 2),
            'interest_payment': round(interest_payment, 2),
            'principal_payment': round(principal_payment, 2),
            'remaining_balance': round(remaining_balance, 2)
        })
        current_date += relativedelta(months=1)
        total_payment += monthly_payment
    # Переплата - это разница между общей суммой выплат и основной суммой кредита
    overpayment = total_payment - amount
    return total_payment, overpayment, payments