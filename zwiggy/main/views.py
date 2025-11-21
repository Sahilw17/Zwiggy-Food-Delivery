from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse
from .models import Restaurant, MenuItem, CartItem
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from django.db import models
from django.contrib.auth.decorators import login_required
from .models import Restaurant, MenuItem, CartItem, Order, OrderItem
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from decimal import Decimal



def home(request):
    restaurants = Restaurant.objects.all()
    # show some menu items on the home page too
    menu_items = MenuItem.objects.select_related('restaurant').all()[:12]
    # compute cart count (session or DB)
    cart_count = _get_cart_count(request)
    return render(request, 'main/home.html', {
        'restaurants': restaurants,
        'menu_items': menu_items,
        'cart_count': cart_count,
    })

def restaurants(request):
    restaurants = Restaurant.objects.prefetch_related('menu_items').all()
    cart_count = _get_cart_count(request)
    return render(request, 'main/restaurants.html', {
        'restaurants': restaurants,
        'cart_count': cart_count,
    })

def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        if not username or not password:
            return render(request, 'main/signup.html', {'error': 'Username and password required.'})
        if User.objects.filter(username=username).exists():
            return render(request, 'main/signup.html', {'error': 'Username already taken.'})
        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)
        return redirect('home')
    return render(request, 'main/signup.html')

def login_view(request):
    next_url = request.GET.get('next')  # if coming from /cart/
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)

            # Merge guest cart if exists
            _merge_session_cart_to_db(request, user)

            # Redirect user to the original page they came from
            if next_url:
                return redirect(next_url)
            return redirect('home')

        else:
            return render(request, 'main/login.html', {
                'error': 'Invalid credentials.',
                'next': next_url
            })
    
    return render(request, 'main/login.html', {'next': next_url})

def logout_view(request):
    logout(request)
    return redirect('home')

# ---------- Cart helpers & views ----------

def _get_cart_count(request):
    if request.user.is_authenticated:
        return CartItem.objects.filter(user=request.user).aggregate(total=models.Sum('quantity'))['total'] or 0
    else:
        session_cart = request.session.get('cart', {})  # {item_id: qty}
        return sum(session_cart.values()) if session_cart else 0

def _merge_session_cart_to_db(request, user):
    """Merge session cart into DB cart after login."""
    session_cart = request.session.get('cart', {})
    if not session_cart:
        return
    for item_id, qty in session_cart.items():
        try:
            menu_item = MenuItem.objects.get(id=item_id)
        except MenuItem.DoesNotExist:
            continue
        cart_item, created = CartItem.objects.get_or_create(user=user, item=menu_item)
        if not created:
            cart_item.quantity += int(qty)
        else:
            cart_item.quantity = int(qty)
        cart_item.save()
    # clear session cart
    request.session['cart'] = {}

def add_to_cart(request, item_id):
    """
    Accepts POST (preferred) or GET (fallback) to add item to cart.
    If user is authenticated -> saved in DB (CartItem).
    If guest -> saved in session (request.session['cart'] = {id: qty})
    """
    menu_item = get_object_or_404(MenuItem, id=item_id)
    if request.method == 'POST' or request.method == 'GET':
        if request.user.is_authenticated:
            cart_item, created = CartItem.objects.get_or_create(user=request.user, item=menu_item)
            if not created:
                cart_item.quantity += 1
            cart_item.save()
        else:
            session_cart = request.session.get('cart', {})
            session_cart[str(menu_item.id)] = int(session_cart.get(str(menu_item.id), 0)) + 1
            request.session['cart'] = session_cart
    return redirect(request.POST.get('next') or request.META.get('HTTP_REFERER') or reverse('home'))

def remove_from_cart(request, item_id):
    """Remove one quantity; if quantity becomes 0 remove key."""
    menu_item = get_object_or_404(MenuItem, id=item_id)
    if request.user.is_authenticated:
        try:
            cart_item = CartItem.objects.get(user=request.user, item=menu_item)
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete()
        except CartItem.DoesNotExist:
            pass
    else:
        session_cart = request.session.get('cart', {})
        key = str(menu_item.id)
        if key in session_cart:
            if session_cart[key] > 1:
                session_cart[key] -= 1
            else:
                del session_cart[key]
            request.session['cart'] = session_cart
    return redirect('view_cart')

@login_required(login_url='login')
def view_cart(request):

    if request.user.is_authenticated:
        items = CartItem.objects.filter(user=request.user).select_related('item')
        cart_items = [{
            'id': ci.item.id,
            'name': ci.item.name,
            'qty': ci.quantity,
            'price': ci.item.price,
            'total': ci.total_price(),
            'image': ci.item.image.url if ci.item.image else None
        } for ci in items]
        total = sum(ci.total_price() for ci in items)
    else:
        session_cart = request.session.get('cart', {})  # keys are strings
        cart_items = []
        total = Decimal('0.00')
        for id_str, qty in session_cart.items():
            try:
                mi = MenuItem.objects.get(id=int(id_str))
            except MenuItem.DoesNotExist:
                continue
            subtotal = mi.price * int(qty)
            total += subtotal
            cart_items.append({
                'id': mi.id,
                'name': mi.name,
                'qty': qty,
                'price': mi.price,
                'total': subtotal,
                'image': mi.image.url if mi.image else None
            })
    return render(request, 'main/cart.html', {
        'cart_items': cart_items,
        'total': total,
        'cart_count': _get_cart_count(request),
    })
@login_required
def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user)

    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect('view_cart')

    # Total
    total_amount = sum(ci.item.price * ci.quantity for ci in cart_items)

    # Get restaurant delivery time from first item
    restaurant = cart_items.first().item.restaurant
    delivery_time_text = restaurant.delivery_time  # "30-40 mins"

    # extract integer avg minutes
    try:
        mins = delivery_time_text.replace("mins", "").strip()
        if "-" in mins:
            a, b = mins.split("-")
            delivery_minutes = (int(a) + int(b)) // 2
        else:
            delivery_minutes = int(mins)
    except:
        delivery_minutes = 30  # fallback

    # Create order
    order = Order.objects.create(
        user=request.user,
        total=total_amount,
        delivery_minutes=delivery_minutes
    )

    # Order items
    for ci in cart_items:
        OrderItem.objects.create(
            order=order,
            menu_item=ci.item,
            quantity=ci.quantity,
            price=ci.item.price
        )

    cart_items.delete()

    return redirect('order_success', order_id=order.id)

@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, "main/order_success.html", {"order": order})

@login_required
def track_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, "main/track_order.html", {"order": order})
