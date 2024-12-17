import csv
import time
import os

class CsvUpdater:
    #def __init__(self, csv_file):
        #self.csv_file = csv_file

    def create_new_order(self, order_id, input_token, output_token, making_amount, taking_amount, transaction_hash):

        # Append order details to orders.csv
        # Ensure CSV file has headers and append order details
        file_exists = os.path.isfile('orders.csv')
        with open('orders.csv', mode='a', newline='') as file:
            fieldnames = ['Order ID','Input Token', 'Output Token', 'Making Amount', 'Taking Amount', 'Price', 'Timestamp', 'Transaction Hash', 'Transaction Status', 'Order Status', 'Fills']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerow({
                'Order ID': order_id,
                'Input Token': input_token,
                'Output Token': output_token,
                'Making Amount': making_amount,
                'Taking Amount': taking_amount,
                'Price': float(taking_amount) / float(making_amount),
                'Timestamp': time.time(),
                'Transaction Hash': transaction_hash,
                'Transaction Status': 'Submitted',
                'Order Status': 'Open',
                'Fills': []
            })

    def update_orders_csv(self, order_id, fieldname, value):

        try:

            with open('orders.csv', mode='r') as file:
                reader = csv.DictReader(file)
                orders = list(reader)
            
            for order in orders:
                #print(order)
                if order['Order ID'] == order_id:
                    if order[fieldname] != value:
                        #print("updating orders.csv", order_id, fieldname, value)
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
        except Exception as e:
            print("error updating orders.csv", order_id, fieldname, value)
