from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login
from django.utils import timezone

from .. import models
from .. import utils as tools
from .constants import APPROVED_USERS
import json, datetime, io, csv


def admin_page(request):
    if not request.user.is_authenticated:
        logged = False
        if request.method == "POST":
            if "username" in request.POST:
                username = request.POST["username"]
                password = request.POST["password"]
                user = authenticate(request, username=username, password=password)
                if (user is not None) and (username in APPROVED_USERS):
                    login(request, user)
                    logged = True
        if not logged:
            return render(request, 'admin-login.html')
    views,visitors,orders = tools.get_analytic_data()
    context = {
        "views": views,
        "orders": orders,
        "visitors": visitors
    }
    return render(request, 'admin.html', context=context)

@csrf_exempt
def upload_image(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if (user is not None) and (username in APPROVED_USERS):
            login(request, user)
            url_mode = request.POST['urls']
            if url_mode == "file":
                urls = tools.save_images(request.FILES, request.POST["sku"], request.POST["title"])
            else:
                urls = tools.download_images(json.loads(request.POST["urls"]), request.POST["sku"], request.POST["title"])
            return HttpResponse(f"Success - Images uploaded: {json.dumps(urls)}")
    return HttpResponse("Failure")

@csrf_exempt
def get_orders(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if (user is not None) and (username in APPROVED_USERS):
            login(request, user)
            last_check = timezone.now() + datetime.timedelta(minutes=-10)
            orders = models.Orders.objects.filter(sale_date__gte=last_check)
            orders.update(checked=True)
            for item in orders:
                item.save()
            skus = []
            for order in orders:
                skus.append(order.sku)
            if not orders:
                return HttpResponse("No Orders")
            else:
                return HttpResponse(json.dumps(skus))
    return HttpResponse("Failure")

@csrf_exempt
def upload_item(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if (user is not None) and (username in APPROVED_USERS):
            login(request, user)
            item = json.loads(request.POST["item"])
            try:
                dupe_item = models.Jean.objects.get(sku=item["sku"])
                return HttpResponse("Failure - Item is a duplicate")
            except models.Jean.DoesNotExist:
                new_item = models.Jean(**item)
                new_item.save()
                return HttpResponse("Success")
    return HttpResponse("Failure")

@csrf_exempt
def delete_item(request):
    if request.method != "POST":
        return HttpResponse("Failure")
    if not request.user.is_authenticated:
        logged = False
        if "username" in request.POST:
            username = request.POST["username"]
            password = request.POST["password"]
            user = authenticate(request, username=username, password=password)
            if (user is not None) and (username in APPROVED_USERS):
                login(request, user)
                logged = True
        if not logged:
            return HttpResponse("Failure")

    sku = request.POST["sku"]
    try:
        models.Jean.objects.filter(sku=sku).delete()
    except models.Jean.DoesNotExist:
        pass
    if "website_order" in request.POST:
        if request.POST["website_order"] == "no":
            try:
                tools.delete_folder(f"staticfiles/media/product-images/{sku}")
            except ValueError:
                return HttpResponse("Failure")
    if "stay" in request.POST:
        return redirect("/admin_page/")
    return HttpResponse("Success")

@csrf_exempt
def get_orders_csv(request):
    if request.method == "POST":
        if "username" in request.POST:
            username = request.POST["username"]
            password = request.POST["password"]
            user = authenticate(request, username=username, password=password)
            if (user is not None) and (username in APPROVED_USERS):
                login(request, user)

                orders_data = tools.get_order_data()
                buffer = io.StringIO()
                writer = csv.writer(buffer)
                writer.writerows(orders_data)

                buffer.seek(0)
                response = HttpResponse(buffer, content_type="text/csv")
                response["Content-Disposition"] = "attachment; filename=lovedjeans_orders.csv"
                return response
    return HttpResponse("")

@csrf_exempt
def get_stock_csv(request):
    if request.method == "POST":
        if "username" in request.POST:
            username = request.POST["username"]
            password = request.POST["password"]
            user = authenticate(request, username=username, password=password)
            if (user is not None) and (username in APPROVED_USERS):
                login(request, user)

                orders_data = tools.get_stock_data()
                buffer = io.StringIO()
                writer = csv.writer(buffer)
                writer.writerows(orders_data)

                buffer.seek(0)
                response = HttpResponse(buffer, content_type="text/csv")
                response["Content-Disposition"] = "attachment; filename=lovedjeans_stock.csv"
                return response
    return HttpResponse("")

@csrf_exempt
def get_deleter_status(request):
    if request.method == "POST":
        if "username" in request.POST:
            username = request.POST["username"]
            password = request.POST["password"]
            user = authenticate(request, username=username, password=password)
            if (user is not None) and (username in APPROVED_USERS):
                login(request, user)
                return HttpResponse(str(tools.is_deleter_running()))
    return HttpResponse("")
