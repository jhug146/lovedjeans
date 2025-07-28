from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', views.index, name='index'),
    path('add_to_cart/', views.add_to_cart),
    path('remove_from_cart/', views.remove_from_cart),
    path('items/', views.items, name='items'),
    path('item/<sku>', views.item, name='item'),
    path('products/<sku>', views.item),
    path('collections/', views.items),
    path('collections/<t1>', views.items),
    path('collections/<t1>/<t2>', views.items),
    path('collections/<t1>/<t2>/<t3>', views.items),
    path('collections/<t1>/<t2>/<t3>/<t4>', views.items),
    path('collections/<t1>/<t2>/<t3>/<t4>/<t5>', views.items),
    path('cart/', views.cart, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('returns/', views.returns, name='returns'),
    path('contact_form/', views.contact_form, name='contact_form'),
    path('shipping/', views.shipping, name='shipping'),
    path('sizing/', views.sizing, name='sizings'),
    path('contact/', views.contact, name='contact'),
    path('terms/', views.terms, name='terms'),
    path('faq/', views.faq, name='faq'),
    path('refunds/', views.refunds, name='refunds'),
    path('session/<key>', views.get_var, name='get_var'),
    path('upload_image/', views.upload_image),
    path('upload_item/', views.upload_item),
    path('get_orders/', views.get_orders),
    path('delete_item/', views.delete_item, name='delete_item'),
    path('checkout_captcha', views.checkout_captcha, name='checkout_captcha'),
    path('payment/', views.payment, name='payment'),
    path('make_payment/', views.make_payment, name='make_payment'),
    path('execute_payment/', views.execute_payment, name='execute_payment'),
    path('payment_done/', views.payment_done, name='payment_done'),
    path('admin_page/', views.admin_page, name='admin_page'),
    path('get_csv_orders/', views.get_orders_csv),
    path('get_csv_stock/', views.get_stock_csv)
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
