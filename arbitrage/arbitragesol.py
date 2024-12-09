from solana.rpc.api import Client
import requests
import time

# Solana RPC Endpoint
SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"
client = Client(SOLANA_RPC_URL)

# Token Addresses (Example: USDC and SOL)
TOKEN_USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"  # USDC
TOKEN_SOL = "So11111111111111111111111111111111111111112"  # SOL (native token)

# DEX API Endpoints
SERUM_API = "https://serum-api.bonfida.com/markets"
RAYDIUM_API = "https://api.raydium.io/pairs"

# Helper Function to Fetch Prices
def get_serum_price():
    try:
        response = requests.get(SERUM_API).json()
        for market in response:
            if market["name"] == "SOL/USDC":
                return float(market["price"])
    except Exception as e:
        print(f"Error fetching Serum price: {e}")
    return None

def get_raydium_price():
    try:
        response = requests.get(RAYDIUM_API).json()
        for pair in response:
            if pair["name"] == "SOL-USDC":
                return float(pair["price"])
    except Exception as e:
        print(f"Error fetching Raydium price: {e}")
    return None

# Arbitrage Opportunity Tracker
def track_arbitrage(opportunity_threshold=0.01):
    while True:
        raydium_price = get_raydium_price()
        serum_price = get_serum_price()

        if serum_price and raydium_price:
            # Calculate Arbitrage Opportunity
            price_diff = abs(serum_price - raydium_price)
            profit_percentage = price_diff / min(serum_price, raydium_price)

            if profit_percentage > opportunity_threshold:
                print(f"Arbitrage Opportunity Found!")
                print(f"Serum Price: {serum_price:.2f}, Raydium Price: {raydium_price:.2f}")
                print(f"Profit Percentage: {profit_percentage * 100:.2f}%\n")
            else:
                print(f"No significant arbitrage opportunity. Price Diff: {price_diff:.2f}")

        # Wait before the next check
        time.sleep(5)

# Run the Tracker
track_arbitrage()
