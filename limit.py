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
from cryptog import get_private_key
from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt
from orderchart import OrderChart
from jupiterapi import JupiterAPI
from csv_updater import CsvUpdater  

from order import Order
from cryptotoken import CryptoToken

class JupiterTrade:


    def __init__(self):
        self.csv_updater = CsvUpdater()

        # Set up RPC connection
        #RPC_CONNECTION = Client("https://api.devnet.solana.com")
        self.RPC_CONNECTION = Client("https://api.mainnet-beta.solana.com")
        WALLET_PRIV_KEY = get_private_key()


        self.SOL = CryptoToken(
            address="So11111111111111111111111111111111111111112",
            decimals=9,
            symbol="SOL",
            name="Solana",
            lamports=1_000_000_000,
        )
        self.USDC = CryptoToken(
            address="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            decimals=6,
            symbol="USDC",
            name="USD Coin",
            lamports=1_000_000,
        )

        self.wallet = Keypair.from_bytes(bytes(map(int, WALLET_PRIV_KEY.strip('[]').split(','))))

        self.jupiter_api = JupiterAPI(self.wallet)

        self.order_status = {}
        self.tx_status = {}
        self.buy_tx_status = None
        self.buy_order_status = None

        self.order_chart = OrderChart()

#pub key = H8mSLthifZsBZpG8CbJeNXGGuThr4pNzPZpuQQq7adRC


    def trade(self, token_1, token_2, token_1_amount, valid_for, spread):

        current_price = self.jupiter_api.get_price(token_1, token_2)


        limit_price_buy = float(current_price) * (1 + spread) # Limit price in USDC per SOL

        making_amount = str(int(token_1_amount * token_1.lamports))  #  Amount of input mint to sell (required).
        taking_amount = str(int(token_1_amount * limit_price_buy * token_2.lamports))  # Amount of output mint to buy (required).

        buy_order = self.place_order(token_1, token_2, making_amount, taking_amount, valid_for)



        limit_price_sell = float(current_price) * (1 - spread) # Limit price in USDC per SOL

        making_amount = str(int(token_1_amount * limit_price_sell * token_2.lamports))  #  Amount of input mint to sell (required).
        taking_amount = str(int(token_1_amount * token_1.lamports))  # Amount of output mint to buy (required).

        sell_order = self.place_order(token_2, token_1, making_amount, taking_amount, valid_for)

        return buy_order, sell_order

    def place_order(self, input_token, output_token, making_amount, taking_amount, valid_for):

        response_json = self.jupiter_api.place_order(input_token, output_token, making_amount, taking_amount, valid_for)

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

        print("placed order to buy", making_amount, "of", input_token.symbol, "for", taking_amount, "of", output_token.symbol, ". order id", order, "tx hash", tx_hash.value)
        
        self.csv_updater.create_new_order(order, input_token.symbol, output_token.symbol, making_amount, taking_amount, tx_hash.value)

        order = Order(order, tx_hash.value, input_token, output_token, making_amount, taking_amount, float(taking_amount) / float(making_amount), valid_for)
        # Check transaction status
        #self.order_status[order] = "Placed"
        #self.tx_status[tx_hash.value.__str__()] = "Placed"
        return order


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

            self.csv_updater.update_orders_csv(order_id, "Transaction Status", status.confirmation_status)

            #print(f"Confirmation Status: {status.confirmation_status}")
            #print(f"Slot: {status.slot}")
            #print(f"Confirmations: {status.confirmations}")
            #print(f"Error: {status.err}")
            #print(status.confirmation_status==TransactionConfirmationStatus.Finalized)
            return status.confirmation_status            
        except SolanaRpcException as e:
            print(f"An SolanaRpcException error occurred: {e}")



    def cancel_order(self, order_id):

        self.jupiter_api.cancel_order(order_id)


    def print_order_status(self,label,order):
        tx_id = order.transaction_hash.__str__()
        if(self.tx_status.get(tx_id) != TransactionConfirmationStatus.Finalized):
            self.tx_status[tx_id] = self.check_transaction_status(order.order_id, order.transaction_hash)
            print(f"{label} transaction",self.tx_status.get(tx_id))
        elif (self.order_status.get(order.order_id) != "Closed"):
            open_order = self.jupiter_api.get_open_order(order.order_id)
            if(open_order != None):
                self.order_status[order.order_id] = "Open"
                open_order_expiry = open_order.get('account', {}).get('expiredAt')
                if open_order_expiry:
                    open_order_expiry_time = time.strptime(open_order_expiry, "%Y-%m-%dT%H:%M:%S.%fZ")
                    time_to_expiry = time.mktime(open_order_expiry_time) - time.time()
                    print(f"{label} order open, expires in", round(time_to_expiry), "seconds")
                else:
                    time_to_expiry = None
                    print(f"{label} order open")
            else:
                self.order_status[order.order_id] = "Closed"
                print(f"{label} order closed")
        else:
            order_history = self.jupiter_api.get_history(order.order_id)
            if(order_history != None):
                print(f"{label} order", order_history.get('status'))
            else:
                print(f"{label} order not found")


if __name__ == '__main__':

    service = JupiterTrade()
    token_1 = service.SOL
    token_2 = service.USDC
    token_1_amount = 0.03  # Amount of SOL to sell
    valid_for = 600  # Order valid for in seconds
    spread = 0.002  # Spread in percentage

    buy_order, sell_order = service.trade(token_1, token_2, token_1_amount, valid_for, spread)
    #buy_tx, buy_order = Signature.from_string("5Ba9AZW5zFD4Tak1BPxNEATvAHatVKGvKk4bQkBbS3p2izTXRRDpR1oXZHXccm9cWfoadAV9Er3f73pN9iXhE8xG"), "F1HzsjA7VnnX9MWK2rwe4uu5NvjvqVK4qi9TaFiXwq8r"
    #sell_tx, sell_order = Signature.from_string("464huDGkmvzoQjCrD8fAPc1Ke32XkHYkhn3VbQtjcvJwrbcxd5ccJEbQAJrXEg6E5Bn94aoRiZniyQq8wziHCo5B"), "G5HpHgkWMedwZ6rCCopKbWZjp7BfBYPSSbyQMBFhBVXN"


    #service.update_orders_csv("F1HzsjA7VnnX9MWK2rwe4uu5NvjvqVK4qi9TaFiXwq8r", "Order Status", TransactionConfirmationStatus.Finalized)
    #sell_tx_status = TransactionConfirmationStatus.Finalized
    while True:
        try:
            while True:
            #price = service.get_price(token_1, token_2)
                service.print_order_status("buy", buy_order)
                service.print_order_status("sell", sell_order)
                #service.order_chart.update(time.time(), 1000 * buy_order.price, 1000/sell_order.price, price)
                time.sleep(5)
        except KeyboardInterrupt:
            print("KeyboardInterrupt detected. Cancelling open orders...")
            service.cancel_order(buy_order.order_id)
            service.cancel_order(sell_order.order_id)
            break