import os
import sys

from paypalcheckoutsdk.orders import OrdersCreateRequest, OrdersCaptureRequest
from paypalcheckoutsdk.core import PayPalHttpClient, LiveEnvironment

from .. import models
from .tools import get_shipping


class PayPalClient:
    def __init__(self):
        self.client_id = str(os.environ.get("PAYPAL_CLIENT_ID"))
        self.client_secret = str(os.environ.get("PAYPAL_CLIENT_SECRET"))
        self.environment = LiveEnvironment(client_id=self.client_id, client_secret=self.client_secret)
        self.client = PayPalHttpClient(self.environment)

    def object_to_json(self, json_data):
        result = {}
        if sys.version_info[0] < 3:
            itr = json_data.__dict__.iteritems()
        else:
            itr = json_data.__dict__.items()
        for key,value in itr:
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
                result.append(self.object_to_json(item) if not self.is_primittive(item) \
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
