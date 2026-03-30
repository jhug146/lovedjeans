from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .. import models
from .. import utils as tools
from .constants import WEBSITE_URL
import json


@csrf_exempt
def checkout_captcha(request):
    correct = tools.verify_captcha(request.POST["g-recaptcha-response"])
    return HttpResponse("Success" if correct else "Failure")

def payment(request):
    if request.method == "POST":
        details = request.POST["details"]
        try:
            shipping = json.loads(details)["shipping"]
        except json.JSONDecodeError:
            return HttpResponse("Sorry, there was an error processing your payment: " + str(details))
        cart = tools.get_cart(request)
        items = [models.Jean.objects.get(sku=item['sku']) for item in cart]
        postage = float(tools.get_shipping(shipping["method"], items))
        price = float(tools.cart_total(cart))
        context = {
            "details": details,
            "price": tools.float_to_currency(price),
            "postage": tools.float_to_currency(postage),
            "total": tools.float_to_currency(round(price + postage, 2)),
            "cart": items
        }
        return render(request, "payment.html", context=context)

def make_payment(request):
    if request.method == "POST" and request.META["HTTP_REFERER"] == WEBSITE_URL + "/payment/":
        try:
            content = json.loads(request.body)
        except json.JSONDecodeError:
            return HttpResponse("Error processing payment: " + content)
        response = tools.CreateOrder().create_order(
            content["cart"],
            content["shipping"],
            debug = True
        )
        return JsonResponse(response.id, safe=False)
    return HttpResponse("Error: Payment request is invalid")

def execute_payment(request):
    ID_START = 27091
    if (request.method == "POST") and (request.META["HTTP_REFERER"] == WEBSITE_URL + "/payment/"):
        try:
            body = json.loads(request.body.decode("utf-8"))
            dict_info = body['info'].replace("&quot;", '"')
            info = json.loads(dict_info)
        except json.JSONDecodeError:
            return HttpResponse("Error executing payment: " + request.body.decode("utf-8"))
        tools.CaptureOrder().capture_order(body["orderID"], debug=True)

        order_num = ID_START + models.Orders.objects.all().count()

        item_model = models.Jean.objects.get(sku=info["cart"][0]["sku"])
        item = {
            "gender": item_model.gender,
            "size":   item_model.measuredSize,
            "sku":    item_model.sku
        }
        tools.sale(info['cart'], info['shipping'], order_num)
        request.session['cart'] = []

        details = {
            "item": item,
            "order_id": str(order_num)
        }
        return HttpResponse(json.dumps(details))
    return HttpResponse("Error: Payment execution is invalid")

def payment_done(request):
    if request.method == "POST":
        body = request.POST["details"]
        details = json.loads(body)
        item = details["item"]
        more_items = tools.get_recommended_items(item["gender"], item["size"], item["sku"])
        context = {
            "order_id": details["order_id"],
            "more_items": more_items
        }
        return render(request, 'payment-done.html', context=context)
