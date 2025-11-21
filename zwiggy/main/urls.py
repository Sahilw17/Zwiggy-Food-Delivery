from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin   # ✅ Add this
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),   # ✅ ADD THIS LINE

    path('', views.home, name='home'),
    path('restaurants/', views.restaurants, name='restaurants'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('checkout/', views.checkout, name='checkout'),
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),
    path('track-order/<int:order_id>/', views.track_order, name='track_order'),

    # cart
    path('cart/', views.view_cart, name='view_cart'),
    path('add-to-cart/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
