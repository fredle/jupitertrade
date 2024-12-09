import requests


def get_price(mint):


    # Send request to API server
    response = requests.get(f"https://api.jup.ag/price/v2?ids={mint}",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )

    if response.status_code != 200:
        raise Exception(f"API request failed with status code {response.status_code}: {response.text}")
    
    price = response.json().get("data").get(mint).get("price")
    return price
print(get_price("So11111111111111111111111111111111111111112"))