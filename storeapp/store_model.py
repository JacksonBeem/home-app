# actual logic of the store app

import requests
import os
from dotenv import load_dotenv

# from sqlalchemy.orm import sessionmaker
# from database import engine
# from models.store import Store

# Session = sessionmaker(bind=engine)
# session = Session()

# Load variables from the .env file (it looks for the file in the current or parent directories by default)
load_dotenv()

kroger_token_url = "https://api-ce.kroger.com/v1/connect/oauth2/token"
kroger_location_url = "https://api-ce.kroger.com/v1/locations"
kroger_product_url = "https://api-ce.kroger.com/v1/products"

kroger_secret = os.getenv("KROGER_AUTH")

#print("Kroger Secret:", kroger_secret)  # This will print the value of KROGER_SECRET to verify it's loaded correctly

def bearer_token():
    response = requests.post(
        kroger_token_url,
        data={
            "grant_type": "client_credentials",
            "scope": "product.compact"
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {kroger_secret}"
                
        }
    )
    token_data = response.json()
    access_token = token_data["access_token"]

    return(access_token)

def get_store_data(zipcode):
    # This function will give you the locationid of the store closest to the given zipcode.
    #  You can use this locationid to get the store data.
    response = requests.get(
        kroger_location_url,
        params={
            "filter.zipCode.near": zipcode,
            "filter.limit": 1,
            "filter.radiusInMiles": 50
        },
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {bearer_token()}"
        }
    )
    token_data = response.json()
    location_id = token_data["data"][0]["locationId"]

    return(location_id)

def search_products(query, locationid):
    # This function will search for products based on the query and locationid.
    response = requests.get(
        kroger_product_url,
        params={
            "filter.term": query,
            "filter.locationId": locationid,
            "filter.limit": 14,
            "filter.fulfillment": "ais"
        },
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {bearer_token()}"
        }
    )
    token_data = response.json()
    products = []
    for product in token_data["data"]:
        name = product.get("description", "")
        price = product.get("items", [{}])[0].get("price", {}).get("regular", 0)
        brand = product.get("brand", "")
        size = product.get("items", [{}])[0].get("size", "")
        image_url = ""
        for img in product.get("images", []):
            if img.get("featured", False):
                for size_img in img.get("sizes", []):
                    if size_img.get("size") == "medium":
                        image_url = size_img.get("url")
                        break
                break
        products.append({
            "name": name,
            "price": price,
            "brand": brand,
            "size": size,
            "image_url": image_url
        })
    return products[:14]  # Limit to 14 products