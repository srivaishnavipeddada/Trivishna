from django.urls import path
from . import views
from django.contrib import admin

urlpatterns = [
    path('admin/', admin.site.urls),
    path('custom-admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('', views.home, name='home'),
    path('packages/', views.package_list, name='package_list'),
    path('package/<int:package_id>/', views.package_detail, name='package_detail'),
    path('book/<int:package_id>/', views.book_package, name='book_package'),
    path('upload-payment-proof/<int:booking_id>/', views.upload_payment_proof, name='upload_payment_proof'),
    path('trip-plan/<int:package_id>/', views.generate_trip_plan, name='generate_trip_plan'),
    path('accounts/login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('payment/', views.payment_view, name='payment'),  # Adjusted URL pattern
    path('success/', views.success_view, name='success_view'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('add-to-cart/<int:package_id>/', views.add_to_cart, name='add_to_cart'),
    path('view-cart/', views.view_cart, name='view_cart'),
    path('remove-from-cart/<int:package_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('booking-confirmation/<int:booking_id>/', views.booking_confirmation, name='booking_confirmation'),
    path('cancel-booking/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
]
