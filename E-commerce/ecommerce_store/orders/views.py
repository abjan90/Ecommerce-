from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import Order, OrderItem
from cart.models import Cart, CartItem
from cart.views import get_or_create_cart
import uuid

@login_required
def checkout(request):
    cart = get_or_create_cart(request)
    cart_items = cart.items.all()
    
    if not cart_items:
        messages.error(request, 'Your cart is empty.')
        return redirect('cart:cart_detail')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Calculate totals
                subtotal = cart.total_price
                tax_rate = 0.08  # 8% tax
                tax_amount = subtotal * tax_rate
                total_amount = subtotal + tax_amount
                
                # Create order
                order = Order.objects.create(
                    user=request.user,
                    first_name=request.POST['first_name'],
                    last_name=request.POST['last_name'],
                    email=request.POST['email'],
                    phone=request.POST['phone'],
                    address_line_1=request.POST['address_line_1'],
                    address_line_2=request.POST.get('address_line_2', ''),
                    city=request.POST['city'],
                    state=request.POST['state'],
                    postal_code=request.POST['postal_code'],
                    country=request.POST['country'],
                    subtotal=subtotal,
                    tax_amount=tax_amount,
                    total_amount=total_amount,
                    notes=request.POST.get('notes', ''),
                    payment_status='completed',  # In real app, integrate with payment gateway
                )
                
                # Create order items
                for cart_item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        price=cart_item.product.effective_price,
                    )
                
                # Clear cart
                cart_items.delete()
                
                messages.success(request, 'Your order has been placed successfully!')
                return redirect('orders:order_success', order_number=order.order_number)
                
        except Exception as e:
            messages.error(request, 'There was an error processing your order. Please try again.')
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
    }
    return render(request, 'orders/checkout.html', context)

def order_success(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    return render(request, 'orders/order_success.html', {'order': order})

@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/order_list.html', {'orders': orders})

@login_required
def order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})

