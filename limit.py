import os
import base64
import requests
from solana.rpc.api import Client
from solana.transaction import Transaction
from solders.keypair import Keypair
from solana.transaction import Signature
from solana.rpc.types import TxOpts
from solana.exceptions import SolanaRpcException
from solders.pubkey import Pubkey
from solders.message import Message
from solders.message import to_bytes_versioned 
from solders.transaction import Transaction
from solders.transaction import VersionedTransaction
from solders.transaction_status import TransactionConfirmationStatus
import base58
import time
import json
import csv



class JupiterTrade:

    class Token:
        def __init__(self, address, decimals, symbol, name, lamports):
            self.address = address
            self.decimals = decimals
            self.symbol = symbol
            self.name = name
            self.lamports = lamports

    def __init__(self):


        # Set up RPC connection
        #RPC_CONNECTION = Client("https://api.devnet.solana.com")
        self.RPC_CONNECTION = Client("https://api.mainnet-beta.solana.com")
        with open("private_key.txt", "r") as key_file:
            WALLET_PRIV_KEY = key_file.read().strip()


        self.SOL = self.Token(
            address="So11111111111111111111111111111111111111112",
            decimals=9,
            symbol="SOL",
            name="Solana",
            lamports=1_000_000_000,
        )
        self.USDC = self.Token(
            address="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            decimals=6,
            symbol="USDC",
            name="USD Coin",
            lamports=1_000_000,
        )

        self.wallet = Keypair.from_bytes(bytes(map(int, WALLET_PRIV_KEY.strip('[]').split(','))))

        self.order_status = {}
        self.tx_status = {}
        self.buy_tx_status = None
        self.buy_order_status = None
            

#pub key = H8mSLthifZsBZpG8CbJeNXGGuThr4pNzPZpuQQq7adRC

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
                self.update_orders_csv(order_id, "Fills", transaction['fillPrices'])
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
                self.update_orders_csv(order_id, "Order Status", "Open")
                return order

        return None


    def trade(self):

        token_1 = self.SOL
        token_2 = self.USDC
        token_1_amount = 0.4  # Amount of SOL to sell
        valid_for = 600  # Order valid for in seconds

        current_price = self.get_price(token_1, token_2)

        limit_price = float(current_price) * 1.002 # Limit price in USDC per SOL

        making_amount = str(int(token_1_amount * token_1.lamports))  #  Amount of input mint to sell (required).
        taking_amount = str(int(token_1_amount * limit_price * token_2.lamports))  # Amount of output mint to buy (required).

        buy_tx, buy_order = self.place_order(token_1, token_2, making_amount, taking_amount, valid_for)



        limit_price = float(current_price) * 0.998 # Limit price in USDC per SOL

        making_amount = str(int(token_1_amount * limit_price * token_2.lamports))  #  Amount of input mint to sell (required).
        taking_amount = str(int(token_1_amount * token_1.lamports))  # Amount of output mint to buy (required).

        sell_tx, sell_order = self.place_order(token_2, token_1, making_amount, taking_amount, valid_for)

        return buy_tx, buy_order, sell_tx, sell_order

    def place_order(self, input_mint, output_mint, making_amount, taking_amount, valid_for):

        # Create the request body
        create_order_body = {
            "maker": str(self.wallet.pubkey()),
            "payer": str(self.wallet.pubkey()),
            "inputMint": input_mint.address,  
            "outputMint": output_mint.address, 
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

        order = response_json["order"]

        tx_base64 = response_json["tx"]
        # Deserialize transaction
        tx_bytes = base64.b64decode(tx_base64)

        raw_tx = VersionedTransaction.from_bytes(tx_bytes)
        signature = self.wallet.sign_message(to_bytes_versioned(raw_tx.message))
        signed_tx = VersionedTransaction.populate(raw_tx.message, [signature])

        # Send transaction
        tx_hash = self.RPC_CONNECTION.send_transaction(
            signed_tx,
            #serializeMessage
            opts=TxOpts(skip_preflight=True),
        )

        print("placed order to buy", making_amount, "of", input_mint.symbol, "for", taking_amount, "of", output_mint.symbol, ". order id", order, "tx hash", tx_hash.value)
        
        #print(f"Transaction hash: {tx_hash.value}")
        # Append order details to orders.csv
        # Ensure CSV file has headers and append order details
        file_exists = os.path.isfile('orders.csv')
        with open('orders.csv', mode='a', newline='') as file:
            fieldnames = ['Order ID','Input Token', 'Output Token', 'Making Amount', 'Taking Amount', 'Price', 'Timestamp', 'Transaction Hash', 'Transaction Status', 'Order Status', 'Fills']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerow({
                'Order ID': order,
                'Input Token': input_mint.symbol,
                'Output Token': output_mint.symbol,
                'Making Amount': making_amount,
                'Taking Amount': taking_amount,
                'Price': float(taking_amount) / float(making_amount),
                'Timestamp': time.time(),
                'Transaction Hash': tx_hash.value,
                'Transaction Status': 'Submitted',
                'Order Status': 'Open',
                'Fills': []
            })

        # Check transaction status
        #self.order_status[order] = "Placed"
        #self.tx_status[tx_hash.value.__str__()] = "Placed"
        return tx_hash.value, order


    def check_transaction_status(self, order_id, tx_hash):
        try:
            response = self.RPC_CONNECTION.get_signature_statuses([tx_hash], search_transaction_history=True)

        #print(response.value[0])
        # print(response) 
            try:
                status = response.value[0]
            except:
                print(order_id, "error", status)
                return None
            if(status == None):
                return None

            self.update_orders_csv(order_id, "Transaction Status", status.confirmation_status)

            #print(f"Confirmation Status: {status.confirmation_status}")
            #print(f"Slot: {status.slot}")
            #print(f"Confirmations: {status.confirmations}")
            #print(f"Error: {status.err}")
            #print(status.confirmation_status==TransactionConfirmationStatus.Finalized)
            return status.confirmation_status            
        except SolanaRpcException as e:
            print(f"An SolanaRpcException error occurred: {e}")


        
    def update_orders_csv(self, order_id, fieldname, value):

        #try:

            with open('orders.csv', mode='r') as file:
                reader = csv.DictReader(file)
                orders = list(reader)
            
            for order in orders:
                #print(order)
                if order['Order ID'] == order_id:
                    if order[fieldname] != value:
                        print("updating orders.csv", order_id, fieldname, value)
                        order[fieldname] = value
                    else :
                        return
                    break
            
            with open('orders.csv', mode='w', newline='') as file:
                fieldnames = ['Order ID', 'Input Token', 'Output Token', 'Making Amount', 'Taking Amount', 'Price', 'Timestamp', 'Transaction Hash', 'Transaction Status', 'Order Status','Fills']
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                for order in orders:
                    writer.writerow(order)
        #except Exception as e:
        #    print("error updating orders.csv", order_id, fieldname, value)


    def print_order_status(self,label,order_id,tx):
        tx_id = tx.__str__()
        if(self.tx_status.get(tx_id) != TransactionConfirmationStatus.Finalized):
            self.tx_status[tx_id] = self.check_transaction_status(order_id, tx)
            print(f"{label} transaction",self.tx_status.get(tx_id))
        elif (self.order_status.get(order_id) != "Closed"):
            open_order = self.get_open_order(order_id)
            if(open_order != None):
                self.order_status[order_id] = "Open"
                open_order_expiry = open_order.get('account', {}).get('expiredAt')
                if open_order_expiry:
                    open_order_expiry_time = time.strptime(open_order_expiry, "%Y-%m-%dT%H:%M:%S.%fZ")
                    time_to_expiry = time.mktime(open_order_expiry_time) - time.time()
                    print(f"{label} order open, expires in", round(time_to_expiry), "seconds")
                else:
                    time_to_expiry = None
                    print(f"{label} order open")
            else:
                self.order_status[order_id] = "Closed"
        else:
            order_history = self.get_history(order_id)
            if(order_history != None):
                print(f"{label} order", order_history.get('status'))


service = JupiterTrade()
buy_tx, buy_order, sell_tx, sell_order = service.trade()
#buy_tx, buy_order = Signature.from_string("5Ba9AZW5zFD4Tak1BPxNEATvAHatVKGvKk4bQkBbS3p2izTXRRDpR1oXZHXccm9cWfoadAV9Er3f73pN9iXhE8xG"), "F1HzsjA7VnnX9MWK2rwe4uu5NvjvqVK4qi9TaFiXwq8r"
#sell_tx, sell_order = Signature.from_string("464huDGkmvzoQjCrD8fAPc1Ke32XkHYkhn3VbQtjcvJwrbcxd5ccJEbQAJrXEg6E5Bn94aoRiZniyQq8wziHCo5B"), "G5HpHgkWMedwZ6rCCopKbWZjp7BfBYPSSbyQMBFhBVXN"


#service.update_orders_csv("F1HzsjA7VnnX9MWK2rwe4uu5NvjvqVK4qi9TaFiXwq8r", "Order Status", TransactionConfirmationStatus.Finalized)
#sell_tx_status = TransactionConfirmationStatus.Finalized
while True:
    service.print_order_status("buy",buy_order,buy_tx)
    service.print_order_status("sell",sell_order,sell_tx)
    time.sleep(5)
    