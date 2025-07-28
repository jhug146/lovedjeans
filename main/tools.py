import os
import pathlib
import sys
import time
import threading
import json
from numpy import full
import requests
import urllib.request
from PIL import Image

from . import models
from lovedjeans.settings import BASE_DIR

from paypalcheckoutsdk.orders import OrdersCreateRequest, OrdersCaptureRequest
from django.db.models import Q
from paypalcheckoutsdk.core import PayPalHttpClient, LiveEnvironment

from dotenv import load_dotenv
load_dotenv()

CAPTCHA_SECRET = str(os.environ.get("CAPTCHA_SECRET"))
HOST_URL = "https://www.lovedjeans.co.uk"
IMAGES_URL = os.path.join(HOST_URL, "/staticfiles/media/product-images/")

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

def _send_email(html, subject, email, name):
    headers = {
        "accept": "application/json",
        "api-key": str(os.environ.get("EMAIL_KEY")),
        "content-type": "application/json"
    }
    data = json.dumps({
        "sender": {
            "name": "Loved Jeans",
            "email": "jubblyjeans@gmail.com"
        },
        "to": [{
            "email": email,
            "name": name
        }],
        "subject": subject,
        "htmlContent": html,
        "type": "classic",
        "scheduled_at": time.strftime("%Y-%m-%d %H:%M:%S")
    })
    requests.post(
        "https://api.sendinblue.com/v3/smtp/email",
        data = data,
        headers = headers
    )

def sale(items, shipping, order_num):
    shipping_full = SHIPPING_NAMES[shipping['method']]
    postage = get_shipping(shipping['method'], items)
    address_parts = (shipping['address1'], shipping['address2'], shipping['address3'], shipping['address4'])
    full_address = ", ".join([part.strip() for part in address_parts if part.strip()])

    html = f"""
    <html><head><style>#intro-div * {{color:black}} #details-div * {{color:black}} #total-div * {{color:white}} #items-div * {{color:white}}</style></head><body style='font-family:Helvetica,serif'>
        <div id='intro-div' style='color:black;background-color:#fcfcfc;font-size:16px;width:98%;max-width:660px;margin:1% auto;display:block'>
            <a style='text-decoration:none' href="https://www.lovedjeans.co.uk">
                <p style='text-align:center;color:#B71B17;font-size:36px;margin:1vh 0'>LOVED JEANS</p>
            </a>
            <div>
                <p style='font-size:22px;margin-left:1%'>Thank you for your order!</p>
                <p style='margin-left:2%'>Hi {shipping['firstname'].lower().capitalize()},</p>
                <p style='margin-left:2%'>We have received your order and payment.</p>
                <p style='margin-left:2%'>Your jeans will be dispatched within the next 24 hours.</p>
                <p style='margin-left:2%'>Your tracking number will follow once your order has been dispatched.</p>
            </div>
        <div id='items-div'>
    """
    for item in items:
        item_model = models.Jean.objects.get(sku=item["sku"])
        title = item_model.title
        main_image_url = f"{IMAGES_URL}{item['sku']}/{title.replace(' ', '-')}_0.jpg"
        html += f"""
                <div style='font-size:16px;height:120px;background-color:#133e72;color:white;padding:1vh;margin:0.3% 0'>
                    <!-- {item['sku']} -->
                    <img style='float: left; width: 100px; height:100px; max-width:20vw; max-height: 20vw'
                    src='{main_image_url}'>
                    <p style='margin:3.5% 3%;float:left;display:block;width:50%'>{title}</p>
                    <p style='margin:7% 0 0 2%;float:left;display:block;width:10%;text-align:center'>£{float_to_currency(item['price'])}</p>
                </div>
                """
    html += f"""
        </div><div id='total-div' style='text-align:center;width:100%;float:left;background-color:#133e72;color:white'>
            <p style='float:left;width:50%'>Postage: £{float_to_currency(postage)}</p>
            <p style='float:left;width:50%'>Total: £{float_to_currency(cart_total(items))}</p>
        </div>
        <div id='details-div' style='margin:2% 2% 0 2%;float:left;width:96%'>
            <div style='font-size:16px;width:60%;float:left'>
                <p style='font-size:18px;margin:3% 0 0 0'>Shipping Address: </p>
                <p>{shipping['firstname']} {shipping['surname']}</p>
                <p>{full_address}</p>
                <p>{shipping['country']}</p>
                <p>{shipping['postcode']}</p>
            </div>
            <div style='font-size:18px;width:40%;float:left;text-align:right'>
                <p style='margin:4% 0 1% 0'>Shipping Method</p>
                <p style='margin:1% 0 0.5% 0;font-size:16px'>{shipping_full}</p>
                <p style='margin:5% 0 1% 0'>Order ID</p>
                <p style='margin:1% 0 0.5% 0;font-size:16px'>#{order_num}</p>
            </div>
        </div>
        </div></body></html>
            """
    threading.Thread(target=_send_email, args=(html, "Item Sold On https://lovedjeans.co.uk", "hanzomain901@gmail.com", "James")).start()
    threading.Thread(target=_send_email, args=(html, "Item Sold On https://lovedjeans.co.uk", "jubblyjeans@gmail.com", "Sara/Andrew")).start()
    threading.Thread(target=_send_email, args=(html, "Loved Jeans - Thank You For Your Order", shipping['email'], shipping['firstname'])).start()

    for item in items:
        shipping_string = ""
        for detail in shipping.values():
            shipping_string += detail + ","
        shipping_string += SHIPPING_NAMES[shipping['method']]
        new_order = models.Orders(
            shipping = shipping_string,
            title = item['title'],
            sku = item['sku']
        )
        new_order.save()

    for item in items:
        models.Jean.objects.filter(sku=item['sku']).delete()


def question(request):
    email = request.POST['email']
    message = request.POST['info']
    html = (
        "<div style='width: 25%; margin: 1vh 37.5%; border: 1px solid black; border-radius: 10px; background-color: #133e72;'>"
        f"<p style='font-family: Arial; font-size: 18px; color: white; text-decoration:none; margin: 0.5vw;'>You have received a question on the lovedjeans website</p>"
        f"<p style='font-family: Arial; font-size: 18px; color: white; text-decoration:none; margin: 0.5vw;'><a style='text-decoration:none; color:white;'>{email}</a> asked:</p>"
        f"<p style='white-space: pre-wrap; font-family: Arial; font-size: 18px; background-color: white; color: black; text-decoration:none; margin: 0.5vw;''>{message}</p></div>"
    )
    threading.Thread(target=_send_email, args=(html, "Question Asked On https://lovedjeans.co.uk", "hanzomain901@gmail.com", "James")).start()

def save_images(images, sku, title):
    image_folder = os.path.join(BASE_DIR, pathlib.Path("staticfiles/media/product-images"), sku)
    urls = []
    try:
        os.mkdir(image_folder)
    except FileExistsError:
        pass
    image_files = [None] * 12
    for key,value in images.items():
        image_files[int(key[4])] = value
    for i,image in enumerate(image_files):
        if not image:
            continue
        fixed_title = title.replace(" ", "-")
        img = Image.open(image)
        img_save_location = os.path.join(image_folder, f"{fixed_title}_{i}.jpg")
        img.save(img_save_location)
        urls.append((IMAGES_URL + sku + f"/{fixed_title}_{i}.jpg").replace("'",'"'))
    return urls

def download_images(urls, sku, title):
    image_folder = os.path.join(BASE_DIR, pathlib.Path("staticfiles/media/product-images"), sku)
    try:
        os.mkdir(image_folder)
    except FileExistsError:
        pass
    for i,url in enumerate(urls):
        fixed_title = title.replace(" ", "-")
        image = urllib.request.urlopen(url)
        image = Image.open(image)
        save_location = os.path.join(image_folder, f"{fixed_title}_{i}.jpg")
        image.save(save_location)
    return urls


class PayPalClient:
    def __init__(self):
        self.client_id = str(os.environ.get("PAYPAL_CLIENT_ID"))
        self.client_secret = str(os.environ.get("PAYPAL_CLIENT_SECRET"))

        """Set up and return PayPal Python SDK environment with PayPal access credentials.
           This sample uses SandboxEnvironment. In production, use LiveEnvironment."""

        self.environment = LiveEnvironment(client_id=self.client_id, client_secret=self.client_secret)

        """ Returns PayPal HTTP client instance with environment that has access
            credentials context. Use this instance to invoke PayPal APIs, provided the
            credentials have access. """
        self.client = PayPalHttpClient(self.environment)

    def object_to_json(self, json_data):
        """
        Function to print all json data in an organized readable manner
        """
        result = {}
        if sys.version_info[0] < 3:
            itr = json_data.__dict__.iteritems()
        else:
            itr = json_data.__dict__.items()
        for key,value in itr:
            # Skip internal attributes.
            if key.startswith("__"):
                continue
            result[key] = self.array_to_json_array(value) if isinstance(value, list) else\
                        self.object_to_json(value) if not self.is_primittive(value) else\
                         value
        return result
    def array_to_json_array(self, json_array):
        result = []
        if isinstance(json_array, list):
            for item in json_array:
                result.append(self.object_to_json(item) if  not self.is_primittive(item) \
                              else self.array_to_json_array(item) if isinstance(item, list) else item)
        return result

    def is_primittive(self, data):
        return isinstance(data, str) or isinstance(data, unicode) or isinstance(data, int)


class CreateOrder(PayPalClient):

  SHIPPING_COSTS = {
    "UK-1": ["UK - Royal Mail Tracked 48", 0, 0],
    "UK-2": ["UK - Royal Mail Tracked 24", 0.99, 0.99],
    "EUR": ["Rest Of Europe - Royal Mail International Tracked", 8.5, 5],
    "ROW": ["North/South America and Asia - Royal Mail International Tracked", 15.5, 5]
  }
  def create_order(self, items, shipping, debug=False):
      request = OrdersCreateRequest()
      request.prefer('return=representation')
      request.request_body(self.build_request_body(items, shipping))
      response = self.client.execute(request)
      if response.result.status == "CREATED":
          print("Paypal order made", response.result.__dict__)
          return response.result
      else:
          raise Exception("Error with Paypal", response.result)

  def build_request_body(self, items, shipping):
      shipping_cost = get_shipping(shipping['method'], items)
      total_cost = 0
      order_items = []
      for item in items:
          get_item = models.Jean.objects.get(sku=item["sku"])
          total_cost += get_item.price
          to_add = {
              "name": get_item.title,
              "sku": item["sku"],
              "quantity": "1",
              "unit_amount": {
                "currency_code": "GBP",
                "value": str(get_item.price)
              },
              "category": "PHYSICAL_GOODS"
          }
          order_items.append(to_add)

      request = {
          "intent": "CAPTURE",
          "application_context": {
            "brand_name": "Luv Jeans Ltd",
            "landing_page": "BILLING",
            "shipping_preference": "NO_SHIPPING",
            "user_action": "PAY_NOW"
          },
          "purchase_units": [
            {
              "reference_id": "PUHF",
              "description": "Jeans from lovedjeans.co.uk",
              "custom_id": ",".join([item["sku"] for item in items]),
              "soft_descriptor": "Luv Jeans Ltd",
              "amount": {
                "currency_code": "GBP",
                "value": str(round(total_cost + shipping_cost, 2)),
                "breakdown": {
                  "item_total": {
                    "currency_code": "GBP",
                    "value": str(round(total_cost, 2))
                  },
                  "shipping": {
                    "currency_code": "GBP",
                    "value": str(round(shipping_cost, 2))
                  }
                }
              },
              "items": order_items,
              "shipping": {
                "method": self.SHIPPING_COSTS[shipping['method']][0],
                "address": {
                  "name": {
                    "full_name": shipping["firstname"] + " " + shipping["surname"],
                  },
                  "address_line_1": shipping["address1"],
                  "address_line_2": shipping["address2"],
                  "admin_area_2": shipping["address3"],
                  "admin_area_1": shipping["address4"],
                  "postal_code": shipping["postcode"],
                  "country_code": shipping["country"]
                }
              }
            }
          ]
      }
      return request

class CaptureOrder(PayPalClient):
    def capture_order(self, order_id, debug=False):
      request = OrdersCaptureRequest(order_id)
      response = self.client.execute(request)
      return response

def get_recommended_items(gender, size, sku):
    items = models.Jean.objects.filter(gender=gender, measuredSize=size).filter(~Q(sku=sku)).order_by("?")[:4]
    return items

def get_analytic_data():
    #Views
    views = []
    for view in models.Views.objects.all():
        if view.name == "/":
            name = "Home Page"
        else:
            name = view.name[1:]

        views.append({
            "name": name,
            "count": view.views
        })

    #Visitors and orders
    months = ("Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec")
    visitors_orders = []
    final = []
    for i,analytics_type in enumerate((models.Sessions.objects.all(), models.Orders.objects.all())):
        visitors_orders.append([])
        for session in analytics_type:
            if i:
                date = session.sale_date
            else:
                date = session.day
            for j,item in enumerate(visitors_orders[i]):
                if item[0] == date:
                    visitors_orders[i][j][1] += 1
                    break
            else:
                visitors_orders[i].append([date, 1])
        visitors_orders[i].sort(key=lambda x:x[0])
        final.append([])
        for visit in visitors_orders[i]:
            final[i].append((f"{visit[0].day}-{months[visit[0].month - 1]}", visit[1]))

    return json.dumps(views),json.dumps(final[0]),json.dumps(final[1])

def get_order_data():
    orders = models.Orders.objects.all()
    orders_data = []
    for order in orders:
        orders_data.append((
            order.shipping,
            order.title,
            order.sku,
            order.sale_date
        ))
    return orders_data

def get_images(sku):
    image_folder = os.path.join(BASE_DIR, pathlib.Path("static_files/media/product-images"), sku)
    images = []
    for image in os.listdir(image_folder):
        images.append(f"{IMAGES_URL}{sku}/{image}")
    return ";".join(images)

def get_stock_data():
    stock = models.Jean.objects.all()
    stock_data = []
    for item in stock:
        stock_data.append((
            item.sku,
            item.title,
            item.brand,
            item.description.replace(",", ";"),
            HOST_URL + "/item/" + item.sku,
            get_images(item.sku),
            item.price,
            item.colour,
            item.size,
            item.gender
        ))
    return stock_data

def get_views(sku):
    total = 0
    views = models.Views.objects.filter(sku=sku)
    for day in views:
        total += day.views
    return total

def delete_folder(path):
    os.system(f"rm -r {path}")

def verify_captcha(code):
    response = requests.post(
        "https://www.google.com/recaptcha/api/siteverify",
        data = {
            "secret": CAPTCHA_SECRET,
            "response": code
        }
    )
    return response.json()["success"]

def get_cart(request):
    cart = request.session.get("cart", [])
    items = []
    for item in cart:
        if item.get("price") and models.Jean.objects.filter(sku=item["sku"]).exists():
            items.append(item)
    return items

def cart_total(cart):
    total = 0.0
    for item in cart:
        total += float(item["price"])
    return str(round(total, 2))

def float_to_currency(amount):
    return "{:.2f}".format(float(amount))
