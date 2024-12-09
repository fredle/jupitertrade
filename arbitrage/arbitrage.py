from web3 import Web3
import requests
import time

# Connect to Ethereum Node
INFURA_URL = "https://mainnet.infura.io/v3/b018e54a0aa3433290f38dd732c6273e"
web3 = Web3(Web3.HTTPProvider(INFURA_URL))


TOKEN_A = Web3.to_checksum_address("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eb48")
TOKEN_B = Web3.to_checksum_address("0x6B175474E89094C44Da98b954EedeAC495271d0F")
UNISWAP_ROUTER = Web3.to_checksum_address("0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f")
SUSHISWAP_ROUTER = Web3.to_checksum_address("0xd9e1CE17f2641F24aE83637ab66a2cca9C378B9F")

# ABI for Router (simplified for fetching prices)
ROUTER_ABI = '''
[
    {
        "constant": true,
        "inputs": [
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"}
        ],
        "name": "getAmountsOut",
        "outputs": [
            {"internalType": "uint256[]", "name": "", "type": "uint256[]"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]
'''

# Initialize Router Contracts
uniswap_router = web3.eth.contract(address=UNISWAP_ROUTER, abi=ROUTER_ABI)
sushiswap_router = web3.eth.contract(address=SUSHISWAP_ROUTER, abi=ROUTER_ABI)

# Helper Function to Fetch Prices
def get_price(router, amount_in, path):
    try:
        price = router.functions.getAmountsOut(amount_in, path).call()
        return web3.from_wei(price[-1], "ether")
    except Exception as e:
        print(f"Error fetching price: {e}")
        return None

# Main Arbitrage Tracker
def track_arbitrage(opportunity_threshold=0.01):
    amount_in = web3.to_wei(1, "ether")  # 1 ETH for simplicity
    path = [TOKEN_A, TOKEN_B]  # Token A -> Token B

    while True:
        # Get prices on both DEXs
        uniswap_price = get_price(uniswap_router, amount_in, path)
        sushiswap_price = get_price(sushiswap_router, amount_in, path)

        if uniswap_price and sushiswap_price:
            # Calculate Arbitrage Opportunity
            price_diff = abs(uniswap_price - sushiswap_price)
            profit_percentage = price_diff / min(uniswap_price, sushiswap_price)

            if profit_percentage > opportunity_threshold:
                print(f"Arbitrage Opportunity Found!")
                print(f"Uniswap Price: {uniswap_price:.6f}, SushiSwap Price: {sushiswap_price:.6f}")
                print(f"Profit Percentage: {profit_percentage * 100:.2f}%\n")
            else:
                print(f"No significant arbitrage opportunity. Price Diff: {price_diff:.6f}")

        # Wait before the next check
        time.sleep(5)

# Run the Tracker
track_arbitrage()
