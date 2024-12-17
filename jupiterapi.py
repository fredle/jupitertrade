
import requests
from csv_updater import CsvUpdater 
import time

class JupiterAPI:
    def __init__(self, wallet):
        self.wallet = wallet
        self.csv_updater = CsvUpdater()

    def get_price(self, buyToken,sellToken):
        #print(f"https://api.jup.ag/price/v2?ids={buyToken.address}&vsToken={sellToken.address}")
        response = requests.get(f"https://api.jup.ag/price/v2?ids={buyToken.address}&vsToken={sellToken.address}",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )

        if response.status_code != 200:
            raise Exception(f"API request failed with status code {response.status_code}: {response.text}")
        #print(response.json())

        price = response.json().get("data").get(buyToken.address).get("price")
        return price

    def get_history(self, order_id):

        response = requests.get(f"https://api.jup.ag/limit/v2/orderHistory?wallet={self.wallet.pubkey()}",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )
        if response.status_code != 200:
            raise Exception(f"API request failed with status code {response.status_code}: {response.text}")
        
        orders = response.json().get('orders', [])
        transactions = []

        #price = response.json().get("data").get(mint).get("price")
        for order in orders:
            if order.get('orderKey') == order_id:
                transaction = {
                    'orderKey': order.get('orderKey'),
                    'status': order.get('status'),
                    'filled': order.get('status') == 'Completed',
                    'fillPrices': []
                }
                if order.get('status') == 'Completed':
                    for trade in order.get('trades', []):
                        fill_price = float(trade.get('inputAmount')) / float(trade.get('outputAmount'))
                        transaction['fillPrices'].append(fill_price)
                transactions.append(transaction)
                print(transaction)
                self.csv_updater.update_orders_csv(order_id, "Fills", transaction['fillPrices'])
                return order

        return None

    def get_open_order(self, order_id):

        response = requests.get(f"https://api.jup.ag/limit/v2/openOrders?wallet={self.wallet.pubkey()}",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )

        if response.status_code != 200:
            raise Exception(f"API request failed with status code {response.status_code}: {response.text}")
        
        #print(response.json())
        orders = response.json()
        for order in orders:
            if order['publicKey'] == order_id:
                #print(order)
                self.csv_updater.update_orders_csv(order_id, "Order Status", "Open")
                return order

        return None

    def place_order(self, input_token, output_token, making_amount, taking_amount, valid_for):

        # Create the request body
        create_order_body = {
            "maker": str(self.wallet.pubkey()),
            "payer": str(self.wallet.pubkey()),
            "inputMint": input_token.address,  
            "outputMint": output_token.address, 
            "params": {
                "makingAmount": making_amount,
                "takingAmount": taking_amount,
                "expiredAt": str(int(time.time()) + valid_for), 
            },
            "computeUnitPrice": "1000000",
        }
    
        # Send request to API server
        response = requests.post(
            "https://api.jup.ag/limit/v2/createOrder",
            json=create_order_body,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )

        if response.status_code != 200:
            raise Exception(f"API request failed with status code {response.status_code}: {response.text}")

        response_json = response.json()

        return response_json
    
    def cancel_order(self, order_id): 
        #https://api.jup.ag/limit/v2/cancelOrders
        cancel_order_body = {
            "maker": str(self.wallet.pubkey()),
            "computeUnitPrice": "auto",
            "orders": [order_id]
        }
        print("Canceling order", order_id)
        response = requests.post(
            "https://api.jup.ag/limit/v2/cancelOrders",
            json=cancel_order_body,
            headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            },
        )

        if response.status_code != 200:
            print("Failed to cancel order", order_id)
            return None
        else:
            print("Cancelled order", order_id)
            response_json = response.json()
            print("Orders cancelled:", response_json.get('txs', []))
            return response_json


    def cancel_all_orders(self):
        #https://api.jup.ag/limit/v2/cancelOrders
        cancel_order_body = {
            "maker": str(self.wallet.pubkey()),
            "computeUnitPrice": "auto",
            "orders": []
        }

        response = requests.post(
            "https://api.jup.ag/limit/v2/cancelOrders",
            json=cancel_order_body,
            headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            },
        )


        if response.status_code != 200:
            print("Failed to cancel order")
            return None
        else:
            print("Cancelled orders")
            response_json = response.json()
            print("Orders cancelled:", response_json.get('txs', []))
            return response_json
