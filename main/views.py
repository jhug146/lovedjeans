from django.shortcuts import render, redirect
from django.template.context_processors import csrf
from django.http import Http404, HttpResponse, HttpResponseNotAllowed, JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django import utils
from django.contrib.auth import authenticate, login
from .forms import SearchForm
from . import tools, models
import json, simplejson, datetime, io, csv
from dotenv import load_dotenv
load_dotenv()


WEBSITE_URL = 'https://www.lovedjeans.co.uk'
CART_MAX_SIZE = 12
APPROVED_USERS = {"sara_hughff", "james_hughff", "order_getter", "image_uploading"}

def index(request):
    return render(request, 'index.html')

def cart(request):
    cart = tools.get_cart(request)
    context = {
        'items': [models.Jean.objects.get(sku=item["sku"]) for item in cart],
        'cart': cart,
        'total': tools.cart_total(cart),
        'js_data': simplejson.dumps(cart)
    }
    return render(request, 'cart.html', context=context)

def checkout(request):
    cart = tools.get_cart(request)
    context = {
        'cart': {'cart': cart},
        'total': tools.cart_total(cart),
        'js_data': simplejson.dumps(cart)
    }
    return render(request, 'checkout.html', context=context)

def returns(request):
    return render(request, 'policies/returns.html')

def shipping(request):
    return render(request, 'policies/shipping.html')

def sizing(request):
    return render(request, 'policies/sizing.html')

def faq(request):
    return render(request, 'policies/faq.html')

def refunds(request):
    return render(request, 'policies/refunds.html')

def contact(request):
    return render(request, 'policies/contact.html')

def terms(request):
    return render(request, 'policies/terms.html')

def items(request, t1="", t2="", t3="", t4="", t5=""):
    #Converts requests from Facebook links that have /collections/ and then all the item specifics into normal requests
    data = {
        'gen': ('men','women'),
        'ws': ('26','27','28','29','30','31','32','33','34','35','36','37','38','39','40','42','48','50'),
        'il': ('26','28','30','32','34','36','38','40'),
        'st': ('Straight','Slim','Skinny','Relaxed','Regular','Flared','Classic','Bootcut','Tapered','Wide-Leg'),
        'br': ('7 For All Mankind','AllSaints','Diesel','EDWIN','G-Star','HUGO BOSS','Lee','Levis','Nudie','Replay','SuperDry','Tommy Hilfiger','Wrangler'),
        'col': ('Blue','Black','Grey','Red','White','Green','Yellow','Pink'),
    }
    if t1:
        args = "-".join((t1,t2,t3,t4,t5))
        red_params = []
        for k,v in data.items():
            for val in v:
                if val.lower() in args:
                    red_params.append(f"{k}={val}")

        joined_params = "&".join(red_params)
        return HttpResponseRedirect(f"/items/?{joined_params}")

    if request.method == 'GET':
        form = SearchForm(request.GET)
        if form.is_valid():
            vals = {}
            req = dict(request.GET)
            for param in ('gen','ws','il','br','st','col','cl','con','search','pg','ord'):
                if param in req:
                    vals[param] = req[param]

            search = models.SearchManager()
            results,total = search.search(vals)
            page = (req['pg'][0]) if ('pg' in req) else ("1")
            pages = total // 45 + 1
        form_values = models.FormValues(request.GET)

        brand = gender = ""
        if "gen" in request.GET:
            if "women" in request.GET["gen"]:
                gender = request.GET["gen"].replace("women", "Womens")
            else:
                gender = request.GET["gen"].replace("men", "Mens")
        if "br" in request.GET:
            brand = request.GET["br"]
    else:
        form = SearchForm()
        gender = ""
        brand = ""
        results = []
        form_values = models.FormValues({})

    skus = []
    for item in request.session.get('cart', []):
        skus.append(item['sku'])
    context = {
        'form': form,
        'results': results,
        'query': request.GET,
        'results_number': total,
        'page': page,
        'pages': pages,
        'skus': skus,
        'form_values': form_values,
        'gender': gender,
        'brand': brand
    }
    context.update(csrf(request))
    return render(request, 'items.html', context)

def item(request, sku):
    if request.method == 'GET':
        try:
            current_item = models.Jean.objects.get(sku=sku)
        except models.Jean.DoesNotExist:
            raise Http404('This item no longer exists')
        skus = []
        for item in request.session.get('cart', []):
            skus.append(item['sku'])
        more_items = tools.get_recommended_items(current_item.gender, current_item.measuredSize, current_item.sku)
        context = {
            'more_items': more_items,
            'item': current_item,
            'skus': skus
        }
        return render(request, 'item.html', context=context)

@csrf_exempt
def add_to_cart(request):
    if not tools.is_ajax(request) or not request.method=='POST':
        return HttpResponseNotAllowed(['POST'])
    to_add = {
        'title': request.POST['title'],
        'price': request.POST['price'],
        'sku': request.POST['sku']
    }
    session_cart = tools.get_cart(request)
    full = False
    for item in session_cart:
        if item['sku'] == to_add['sku']:
            break
    else:
        if len(session_cart) < CART_MAX_SIZE and models.Jean.objects.filter(sku=to_add["sku"]).exists():
            session_cart.append(to_add)
        else:
            full = True
    request.session['cart'] = session_cart
    request.session['amount'] = str(len(session_cart))
    request.session['total'] = tools.cart_total(session_cart)
    return HttpResponse(json.dumps({
        "SKU": to_add['sku'],
        "full":  full
    }))

@csrf_exempt
def remove_from_cart(request):
    if not tools.is_ajax(request) or not request.method == 'POST':
        return HttpResponseNotAllowed(['POST'])

    sku = request.POST['sku']
    session_cart = tools.get_cart(request)
    for item in session_cart:
        if item['sku'] == sku:
            session_cart.remove(item)

    request.session['cart'] = session_cart
    request.session['amount'] = str(len(session_cart))
    request.session['total'] = tools.cart_total(session_cart)
    return HttpResponse(sku)

@csrf_exempt
def get_var(request, key):
    if key == 'checkout_info':
        cart = tools.get_cart(request)
        request.session['cart'] = cart
        request.session['amount'] = str(len(cart))
        request.session['total'] = tools.cart_total(cart)
        amount = request.session['amount'] if 'amount' in request.session else '0'
        total = request.session['total'] if 'total' in request.session else '0.00'
        return HttpResponse(f"{amount}:{total}")

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
            last_check = utils.timezone.now() + datetime.timedelta(minutes=-10)
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
            tools.delete_folder(f"staticfiles/media/product-images/{sku}")
    if "stay" in request.POST:
        return redirect("/admin_page/")
    return HttpResponse("Success")

def contact_form(request):
    if tools.verify_captcha(request.POST["g-recaptcha-response"]):
        tools.question(request)
        return render(request, 'policies/contact_complete.html')
    else:
        return render(request, 'policies/contact.html')

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
