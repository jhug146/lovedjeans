from django.shortcuts import render
from django.http import Http404, HttpResponse, HttpResponseNotAllowed, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.template.context_processors import csrf

from .. import models
from .. import utils as tools
from .constants import CART_MAX_SIZE
import json, simplejson


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
        vals = {}
        req = dict(request.GET)
        for param in ('gen','ws','il','br','st','col','cl','con','search','pg','ord'):
            if param in req:
                vals[param] = req[param]

        results,total = models.Jean.objects.search(vals)
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
        gender = ""
        brand = ""
        results = []
        form_values = models.FormValues({})

    skus = []
    for item in request.session.get('cart', []):
        skus.append(item['sku'])
    context = {
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
