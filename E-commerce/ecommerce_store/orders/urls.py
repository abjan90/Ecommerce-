from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('order-success/<str:order_number>/', views.order_success, name='order_success'),
    path('my-orders/', views.order_list, name='order_list'),
    path('order/<str:order_number>/', views.order_detail, name='order_detail'),
]