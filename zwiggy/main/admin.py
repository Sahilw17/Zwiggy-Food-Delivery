from django.contrib import admin
from .models import Restaurant, MenuItem, CartItem

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('name', 'cuisine', 'rating', 'delivery_time')
    search_fields = ('name', 'cuisine')


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'price')
    list_filter = ('restaurant',)
    search_fields = ('name', 'restaurant__name')


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'item', 'quantity', 'created_at')
    list_filter = ('user', 'item')
