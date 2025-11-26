from django.contrib import admin
from .models import Order, OrderItem

# Inline for OrderItem in Order admin
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['total']
    fields = ['product', 'quantity', 'price', 'total']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'user', 'first_name', 'last_name', 
        'total_amount', 'status', 'payment_status', 'created_at'
    ]
    list_filter = [
        'status', 'payment_status', 'payment_method', 
        'created_at', 'updated_at', 'country'
    ]
    search_fields = [
        'order_number', 'user__username', 'user__email', 
        'first_name', 'last_name', 'email', 'phone'
    ]
    list_editable = ['status', 'payment_status']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status', 'payment_status', 'payment_method')
        }),
        ('Customer Information', {
            'fields': (
                ('first_name', 'last_name'),
                'email',
                'phone'
            )
        }),
        ('Shipping Address', {
            'fields': (
                'address_line_1',
                'address_line_2', 
                ('city', 'state'),
                ('postal_code', 'country')
            )
        }),
        ('Order Summary', {
            'fields': (
                ('subtotal', 'tax_amount'),
                ('shipping_cost', 'total_amount')
            )
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Custom actions
    actions = ['mark_as_processing', 'mark_as_shipped', 'mark_as_delivered']
    
    def mark_as_processing(self, request, queryset):
        queryset.update(status='processing')
    mark_as_processing.short_description = "Mark selected orders as Processing"
    
    def mark_as_shipped(self, request, queryset):
        queryset.update(status='shipped')
    mark_as_shipped.short_description = "Mark selected orders as Shipped"
    
    def mark_as_delivered(self, request, queryset):
        queryset.update(status='delivered')
    mark_as_delivered.short_description = "Mark selected orders as Delivered"

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price', 'total']
    list_filter = ['order__status', 'order__created_at']
    search_fields = ['order__order_number', 'product__name']
    readonly_fields = ['total']