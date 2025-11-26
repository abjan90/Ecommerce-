from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from decimal import Decimal
from .models import Order, OrderItem
from cart.models import Cart, CartItem
from cart.views import get_or_create_cart
import uuid
import logging

logger = logging.getLogger(__name__)

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
                # Validate required fields
                required_fields = ['first_name', 'last_name', 'email', 'phone', 
                                 'address_line_1', 'city', 'state', 'postal_code', 'country']
                
                for field in required_fields:
                    if not request.POST.get(field, '').strip():
                        messages.error(request, f'{field.replace("_", " ").title()} is required.')
                        return render(request, 'orders/checkout.html', {
                            'cart': cart,
                            'cart_items': cart_items,
                        })
                
                # Calculate totals with Decimal for precision
                subtotal = Decimal(str(cart.total_price))
                tax_rate = Decimal('0.13')  # 13% VAT for Nepal
                tax_amount = subtotal * tax_rate
                shipping_cost = Decimal('0.00')  # Free shipping
                total_amount = subtotal + tax_amount + shipping_cost
                
                # Create order
                order = Order.objects.create(
                    user=request.user,
                    first_name=request.POST['first_name'].strip(),
                    last_name=request.POST['last_name'].strip(),
                    email=request.POST['email'].strip(),
                    phone=request.POST['phone'].strip(),
                    address_line_1=request.POST['address_line_1'].strip(),
                    address_line_2=request.POST.get('address_line_2', '').strip(),
                    city=request.POST['city'].strip(),
                    state=request.POST['state'].strip(),  # This should match your model field
                    postal_code=request.POST['postal_code'].strip(),
                    country=request.POST['country'].strip(),
                    subtotal=subtotal,
                    tax_amount=tax_amount,
                    shipping_cost=shipping_cost,
                    total_amount=total_amount,
                    notes=request.POST.get('notes', '').strip(),
                    payment_status='pending',  # Change to pending until payment is confirmed
                )
                
                # Create order items
                for cart_item in cart_items:
                    # Check if product is still in stock
                    if cart_item.product.stock_quantity < cart_item.quantity:
                        messages.error(request, f'Insufficient stock for {cart_item.product.name}')
                        return render(request, 'orders/checkout.html', {
                            'cart': cart,
                            'cart_items': cart_items,
                        })
                    
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        price=cart_item.product.effective_price,
                    )
                    
                    # Update product stock
                    cart_item.product.stock_quantity -= cart_item.quantity
                    cart_item.product.save()
                
                # Clear cart
                cart_items.delete()
                
                messages.success(request, 'Your order has been placed successfully!')
                return redirect('orders:order_success', order_number=order.order_number)
                
        except Exception as e:
            logger.error(f"Order processing error: {str(e)}")
            messages.error(request, 'There was an error processing your order. Please try again.')
            # Don't return here, let it fall through to render the form again
    
    # Calculate totals for display
    subtotal = cart.total_price if hasattr(cart, 'total_price') else sum(item.total_price for item in cart_items)
    tax_rate = 13  # 13% for display
    tax_amount = subtotal * Decimal('0.13')
    shipping_cost = Decimal('0.00')
    total_amount = subtotal + tax_amount + shipping_cost
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'tax_rate': tax_rate,
        'tax_amount': tax_amount,
        'shipping_cost': shipping_cost,
        'total_amount': total_amount,
    }
    return render(request, 'orders/checkout.html', context)

@login_required
def order_success(request, order_number):
    """
    Display order success page with complete order details
    """
    try:
        # Get the order with related items
        order = get_object_or_404(
            Order.objects.select_related('user').prefetch_related('items__product'), 
            order_number=order_number, 
            user=request.user
        )
        
        # Calculate order summary
        order_items = order.items.all()
        items_count = sum(item.quantity for item in order_items)
        
        context = {
            'order': order,
            'order_items': order_items,
            'items_count': items_count,
            'customer_name': f"{order.first_name} {order.last_name}",
            'delivery_address': {
                'line_1': order.address_line_1,
                'line_2': order.address_line_2,
                'city': order.city,
                'state': order.state,
                'postal_code': order.postal_code,
                'country': order.country,
            }
        }
        
        return render(request, 'orders/order_success.html', context)
        
    except Order.DoesNotExist:
        messages.error(request, 'Order not found.')
        return redirect('orders:order_list')
    except Exception as e:
        logger.error(f"Error displaying order success: {str(e)}")
        messages.error(request, 'There was an error displaying your order details.')
        return redirect('orders:order_list')

@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/order_list.html', {'orders': orders})

@login_required
def order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})