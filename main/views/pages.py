from django.shortcuts import render

from .. import utils as tools


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

def contact_form(request):
    if tools.verify_captcha(request.POST["g-recaptcha-response"]):
        tools.question(request)
        return render(request, 'policies/contact_complete.html')
    else:
        return render(request, 'policies/contact.html')
