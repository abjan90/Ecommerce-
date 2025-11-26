from .models import Cart

def cart(request):
    cart_items = 0
    cart_total = 0
    
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_items = cart.total_items
            cart_total = cart.total_price
        except Cart.DoesNotExist:
            pass
    else:
        session_key = request.session.session_key
        if session_key:
            try:
                cart = Cart.objects.get(session_key=session_key)
                cart_items = cart.total_items
                cart_total = cart.total_price
            except Cart.DoesNotExist:
                pass
    
    return {
        'cart_items': cart_items,
        'cart_total': cart_total,
    }