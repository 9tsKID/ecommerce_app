from django.urls import path
from .import views
from.views import register_view, login_view, logout_view, admin_dashboard, store_home,  product_detail, add_to_cart, view_cart, remove_from_cart, clear_cart, test_session, checkout, my_orders, start_payment, payment_success, customer_dashboard, load_products_fixture

urlpatterns =[
    path("register/", register_view, name='register'),
    path("login/", login_view, name='login'),
    path("logout/", logout_view, name='logout'),
    path("dashboard/admin", admin_dashboard, name='admin_dashboard'),
    path("", store_home, name='store_home'),
    path('product/<int:product_id>/', product_detail, name='product_detail'),
    path('add-to-cart/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('cart/', view_cart, name='view_cart'),
    path('remove-from-cart/<int:product_id>/', remove_from_cart, name='remove_from_cart'),
    path('clear-cart/', clear_cart, name='clear_cart'),
    path('test-session/', test_session),
    path('checkout/', checkout, name='checkout'),
    path('my-orders/', my_orders, name='my_orders'),
    path('paystack-checkout/', start_payment, name='start_payment'),
    path('payment-success/', payment_success, name='payment_success'),
    path('customer-dashboard/', customer_dashboard, name='customer_dashboard'),
    path('load-products/', load_products_fixture, name='load_products'),




    




]