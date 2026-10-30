import json


class TransactionProcessor:
    def __init__(self, fee_rate):
        self.fee_rate = fee_rate
        self.history = []

    def process_payment(self, sender, receiver, amount, currency="NGN"):
        fee = amount * self.fee_rate
        net_amount = amount - fee
        record = {
            "sender": sender,
            "receiver": receiver,
            "gross": amount,
            "fee": fee,
            "net": net_amount,
            "currency": currency,
        }
        self.history.append(record)
        return record

    def calculate_conversion(self, amount, exchange_rate):
        return amount / exchange_rate

    def export_summary(self, filepath):
        f = open(filepath, "w")
        json.dump(self.history, f)
        f.close()


def filter_high_value(transactions, threshold):
    result = []
    for t in transactions:
        if t["gross"] >= threshold:
            result.append(t)
    return result
  
