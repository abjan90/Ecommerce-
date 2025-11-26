from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Checkout process
    path('checkout/', views.checkout, name='checkout'),
    
    # Order success page
    path('success/<str:order_number>/', views.order_success, name='order_success'),
    
    # Order management
    path('', views.order_list, name='order_list'),
    path('my-orders/', views.order_list, name='my_orders'),  
    
    # Order detail
    path('<str:order_number>/', views.order_detail, name='order_detail'),
]