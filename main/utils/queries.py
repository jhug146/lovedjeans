import json
import os

from django.db.models import Q

from .. import models
from .tools import HOST_URL
from .images import get_images


def get_cart(request):
    cart = request.session.get("cart", [])
    items = []
    for item in cart:
        if item.get("price") and models.Jean.objects.filter(sku=item["sku"]).exists():
            items.append(item)
    return items

def get_recommended_items(gender, size, sku):
    items = models.Jean.objects.filter(gender=gender, measuredSize=size).filter(~Q(sku=sku)).order_by("?")[:4]
    return items

def get_analytic_data():
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

def get_stock_data():
    stock = models.Jean.objects.all()
    stock_data = []
    for item in stock:
        try:
            images = get_images(item.sku)
        except Exception:
            images = ""
        stock_data.append((
            item.sku,
            item.title,
            item.brand,
            item.description.replace(",", ";"),
            HOST_URL + "/item/" + item.sku,
            images,
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

def is_deleter_running():
    try:
        result = os.system("pgrep -f \"^bash ./deleter.sh$\" > /dev/null 2>&1")
        return result == 0
    except Exception:
        return False
