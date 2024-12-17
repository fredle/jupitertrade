

class Order:
    def __init__(self, order_id, transaction_hash, buy_token, sell_token, making_amount, taking_amount, price, valid_for):
        self.order_id = order_id
        self.transaction_hash = transaction_hash
        self.buy_token = buy_token
        self.sell_token = sell_token
        self.making_amount = making_amount
        self.taking_amount = taking_amount
        self.price = price
        self.valid_for = valid_for


