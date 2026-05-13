from django.contrib import admin
from django.utils.html import mark_safe
from .models import Package, Booking, Review, PaymentProof

class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0
    readonly_fields = ('user', 'rating', 'content', 'created_at')

class PackageAdmin(admin.ModelAdmin):
    inlines = [ReviewInline]
    list_display = ('name', 'destination', 'duration', 'price_per_person')
    search_fields = ('name', 'destination')
    list_filter = ('destination',)

class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'package', 'num_travelers', 'preferred_date',
        'contact_info', 'payment_screenshot_display', 'is_verified', 'booked_at'
    )
    search_fields = ('user__username', 'package__name', 'contact_info')
    list_filter = ('is_verified',)

    def payment_screenshot_display(self, obj):
        if obj.payment_screenshot:
            return mark_safe(f'<img src="{obj.payment_screenshot.url}" width="100" height="100" />')
        return 'No Screenshot'
    payment_screenshot_display.short_description = 'Payment Screenshot'

    fieldsets = (
        (None, {
            'fields': (
                'user', 'package', 'num_travelers', 'preferred_date',
                'contact_info', 'payment_screenshot', 'payment_screenshot_display',
                'is_verified', 'booked_at'
            )
        }),
    )
    readonly_fields = ('payment_screenshot_display', 'booked_at')

class PaymentProofAdmin(admin.ModelAdmin):
    list_display = ('email', 'phone', 'booking', 'uploaded_at', 'is_verified')
    list_filter = ('is_verified', 'uploaded_at')
    search_fields = ('email', 'phone', 'booking__id')

admin.site.register(Package, PackageAdmin)
admin.site.register(Booking, BookingAdmin)
admin.site.register(Review)
admin.site.register(PaymentProof, PaymentProofAdmin)
