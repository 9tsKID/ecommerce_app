from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import UserRegistrationForm, ProfileForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from .models import Profile
from .models import Product
from django.http import HttpResponse
from .models import Product, Order, OrderItem
import requests
from django.conf import settings
from django.urls import reverse
from django.http import JsonResponse
from .models import Category
from django.core.paginator import Paginator





def register_view(request):
    if request.method == "POST":
        user_form = UserRegistrationForm(request.POST)
        profile_form = ProfileForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.set_password(user.password)
            user.save()

            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()

            messages.success(request, "Account created successfully.")
            return redirect('login')
    else:
        user_form = UserRegistrationForm()
        profile_form = ProfileForm()

    return render(request, 'store/register.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)

            profile = Profile.objects.get(user=user)
            if profile.role == 'admin':
                return redirect('admin_dashboard')
            else:
                return redirect('customer_dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'store/login.html', {'form': form})



@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('login')


@login_required
def admin_dashboard(request):
    profile = Profile.objects.get(user=request.user)
    if profile.role != 'admin':
        return HttpResponseForbidden("You're not authorized to view this page.")
    
    return render(request, 'store/admin_dashboard.html', {'admin': profile})

def store_home(request):
    query = request.GET.get('q')
    products = Product.objects.all()

    if query:
        products = products.filter(name__icontains=query)

    paginator = Paginator(products, 6)  # Show 6 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'store/store_home.html', {'products': page_obj})


@login_required
def customer_dashboard(request):
    profile = Profile.objects.get(user=request.user)
    return render(request, 'store/customer_dashboard.html', {'profile': profile})



def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'store/product_detail.html', {'product': product})

def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})

    # Increase quantity if already in cart
    if str(product_id) in cart:
        cart[str(product_id)] += 1
    else:
        cart[str(product_id)] = 1

    request.session['cart'] = cart
    return redirect('store_home')

def view_cart(request):
    cart = request.session.get('cart', {})
    products = Product.objects.filter(id__in=cart.keys())

    cart_items = []
    total = 0

    for product in products:
        quantity = cart[str(product.id)]
        subtotal = product.price * quantity
        total += subtotal
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal,
        })

    return render(request, 'store/cart.html', {
        'cart_items': cart_items,
        'total': total
    })


def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    if str(product_id) in cart:
        del cart[str(product_id)]
        request.session['cart'] = cart
    return redirect('view_cart')

def clear_cart(request):
    request.session['cart'] = {}
    return redirect('view_cart')

def test_session(request):
    request.session['test'] = 'hello'
    return HttpResponse(f"Session value: {request.session.get('test')}")


@login_required
def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, "Your cart is empty.")
        return redirect('view_cart')

    products = Product.objects.filter(id__in=cart.keys())

    cart_items = []
    total = 0

    for product in products:
        quantity = cart[str(product.id)]
        subtotal = product.price * quantity
        total += subtotal
        cart_items.append({'product': product, 'quantity': quantity, 'subtotal': subtotal})

    if request.method == 'POST':
        order = Order.objects.create(user=request.user, total_price=total)
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
                price=item['product'].price
            )
        request.session['cart'] = {}  # Clear cart
        messages.success(request, f"Order #{order.id} placed successfully!")
        return redirect('my_orders')

    return render(request, 'store/checkout.html', {'cart_items': cart_items, 'total': total})

@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/my_orders.html', {'orders': orders})


@login_required
def start_payment(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, "Your cart is empty.")
        return redirect('view_cart')

    products = Product.objects.filter(id__in=cart.keys())

    total = 0
    for product in products:
        quantity = cart[str(product.id)]
        total += product.price * quantity

    # Convert total to kobo (Paystack expects lowest currency unit)
    paystack_total = int(total * 100)

    callback_url = request.build_absolute_uri(reverse('payment_success'))

    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "email": request.user.email,
        "amount": paystack_total,
        "callback_url": callback_url
    }

    response = requests.post("https://api.paystack.co/transaction/initialize", headers=headers, json=data)
    res_data = response.json()

    if res_data.get('status'):
        payment_url = res_data['data']['authorization_url']
        return redirect(payment_url)
    else:
        messages.error(request, "Payment failed to initialize.")
        return redirect('view_cart')
    
@login_required
def payment_success(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.info(request, "You already placed the order.")
        return redirect('store_home')

    products = Product.objects.filter(id__in=cart.keys())

    total = 0
    cart_items = []

    for product in products:
        quantity = cart[str(product.id)]
        subtotal = product.price * quantity
        total += subtotal
        cart_items.append({'product': product, 'quantity': quantity})

    # Save order
    order = Order.objects.create(user=request.user, total_price=total)
    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=item['product'],
            quantity=item['quantity'],
            price=item['product'].price
        )

    request.session['cart'] = {}
    messages.success(request, f"Payment successful. Order #{order.id} placed.")
    return redirect('my_orders')

def create_admin(request):
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        return HttpResponse("Superuser created ✅")
    else:
        return HttpResponse("Superuser already exists")
