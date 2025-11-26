from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from orders.models import Order
from cart.views import get_or_create_cart  # Import your cart function
from decimal import Decimal

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Set additional fields
            user.email = request.POST.get('email', '')
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.save()
            
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('home')
    else:
        form = UserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully!')
    return redirect('home')

@login_required
def profile(request):
    """Profile view with user statistics"""
    user = request.user
    
    # Get cart items count using your cart system
    cart_items = 0
    try:
        cart = get_or_create_cart(request)
        cart_items = cart.total_items  # Uses the @property from your Cart model
    except Exception as e:
        # Fallback: try session-based cart
        try:
            if 'cart' in request.session:
                session_cart = request.session['cart']
                cart_items = sum(item['quantity'] for item in session_cart.values())
        except (KeyError, TypeError, AttributeError):
            cart_items = 0
    
    # Get user's orders and statistics
    try:
        user_orders = Order.objects.filter(user=user)
        
        # Include pending orders since your checkout creates orders with payment_status='pending'
        valid_orders = user_orders.filter(payment_status__in=['completed', 'paid', 'pending'])
        
        total_orders = valid_orders.count()
        total_spent = valid_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
        
        # Fix the decimal formatting - round to 2 decimal places
        total_spent = total_spent.quantize(Decimal('0.01'))
        
        recent_orders = user_orders.order_by('-created_at')[:5]  # Show all recent orders regardless of status
        
    except Exception as e:
        # Fallback if Order model doesn't exist or has issues
        total_orders = 0
        total_spent = Decimal('0.00')
        recent_orders = []
    
    context = {
        'user': user,
        'total_orders': total_orders,
        'total_spent': total_spent,
        'cart_items': cart_items,
        'recent_orders': recent_orders,
    }
    
    return render(request, 'accounts/profile.html', context)

@login_required
def edit_profile(request):
    """Edit user profile information"""
    if request.method == 'POST':
        user = request.user
        
        # Update user information
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name = request.POST.get('last_name', '').strip()
        user.email = request.POST.get('email', '').strip()
        
        try:
            user.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('accounts:profile')
        except Exception as e:
            messages.error(request, 'There was an error updating your profile. Please try again.')
    
    return render(request, 'accounts/edit_profile.html', {'user': request.user})

@login_required
def delete_account(request):
    """Delete user account with confirmation"""
    if request.method == 'POST':
        confirm = request.POST.get('confirm_delete')
        if confirm == 'DELETE':
            user = request.user
            logout(request)  # Log out before deleting
            user.delete()
            messages.success(request, 'Your account has been deleted successfully.')
            return redirect('home')
        else:
            messages.error(request, 'Please type "DELETE" to confirm account deletion.')
    
    return render(request, 'accounts/delete_account.html')