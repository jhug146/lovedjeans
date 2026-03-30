import os
import time
import threading
import json
import requests

from .. import models
from .tools import ADMINS, SHIPPING_NAMES, IMAGES_URL, get_shipping, cart_total, float_to_currency

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
    for email, name in ADMINS:
        threading.Thread(target=_send_email, args=(html, "Item Sold On https://lovedjeans.co.uk", email, name)).start()
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
