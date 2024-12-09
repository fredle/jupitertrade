import requests
import base58
import base64
import json
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
from solders import message
from solana.rpc.api import Client
from solana.rpc.types import TxOpts
from solana.rpc.commitment import Processed

# Constants
WALLET_ADDRESS = "H8mSLthifZsBZpG8CbJeNXGGuThr4pNzPZpuQQq7adRC"
INPUT_MINT = "So11111111111111111111111111111111111111112"
OUTPUT_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
AMOUNT = 1

QUOTE_URL = f"https://api.jup.ag/price/v2?ids={INPUT_MINT},{OUTPUT_MINT}"
#QUOTE_URL = f"https://quote-api.jup.ag/v6/quote?inputMint={INPUT_MINT}&outputMint={OUTPUT_MINT}&amount={AMOUNT}"
SWAP_URL = "https://quote-api.jup.ag/v6/swap"
with open('private_key.txt', 'r') as file:
    private_key_ints = json.load(file)
PRIVATE_KEY = Keypair.from_bytes(bytes(private_key_ints))
SOLANA_RPC_URL_ENDPOINT = "https://api.mainnet-beta.solana.com"

print(QUOTE_URL)

# Get quote response
quote_response = requests.get(url=QUOTE_URL).json()
if 'error' in quote_response:
    raise Exception(f"Error fetching quote: {quote_response['error']}")

# Prepare swap payload
payload = {
    "quoteResponse": quote_response,
    "userPublicKey": WALLET_ADDRESS,
    "wrapUnwrapSOL": True
}

print("q", quote_response)

# Get swap transaction route
swap_route = requests.post(url=SWAP_URL, json=payload).json()['swapTransaction']

# Initialize Solana client
client = Client(endpoint=SOLANA_RPC_URL_ENDPOINT)

# Decode and sign the transaction
raw_transaction = VersionedTransaction.from_bytes(base64.b64decode(swap_route))
signature = PRIVATE_KEY.sign_message(message.to_bytes_versioned(raw_transaction.message))
signed_txn = VersionedTransaction.populate(raw_transaction.message, [signature])

# Send the signed transaction
opts = TxOpts(skip_preflight=False, preflight_commitment=Processed)
result = client.send_raw_transaction(txn=bytes(signed_txn), opts=opts)

# Extract and print the transaction ID
transaction_id = json.loads(result.to_json())['result']
print(f"Transaction sent: https://explorer.solana.com/tx/{transaction_id}")