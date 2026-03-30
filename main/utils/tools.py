import os
import requests
from dotenv import load_dotenv
load_dotenv()

CAPTCHA_SECRET = str(os.environ.get("CAPTCHA_SECRET"))
HOST_URL = "https://www.lovedjeans.co.uk"
IMAGES_URL = os.path.join(HOST_URL, "/staticfiles/media/product-images/")

ADMINS = (
    ("hanzomain901@gmail.com", "James"),
    ("jubblyjeans@gmail.com", "Sara"),
    ("andrew.hughff@gmail.com", "Andrew")
)

SHIPPING_COSTS = {
    "UK-1": [0, 0],
    "UK-2": [0.99, 0.99],
    "EUR": [8.5, 5],
    "ROW": [15.5, 5]
}
SHIPPING_NAMES = {
    "UK-1": "UK - Royal Mail Tracked 48",
    "UK-2": "UK - Royal Mail Tracked 24",
    "EUR": "Rest Of Europe - Royal Mail International Tracked",
    "ROW": "Rest Of World - Royal Mail International Tracked"
}

def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

def get_shipping(shipping_type, items):
    shipping_cost = SHIPPING_COSTS[shipping_type][0] + (len(items) - 1) * SHIPPING_COSTS[shipping_type][1]
    return round(shipping_cost, 2)

def verify_captcha(code):
    response = requests.post(
        "https://www.google.com/recaptcha/api/siteverify",
        data = {
            "secret": CAPTCHA_SECRET,
            "response": code
        }
    )
    return response.json()["success"]

def cart_total(cart):
    total = 0.0
    for item in cart:
        total += float(item["price"])
    return str(round(total, 2))

def float_to_currency(amount):
    return "{:.2f}".format(float(amount))
