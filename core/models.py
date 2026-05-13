from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django import forms
from django.core.mail import send_mail
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User


class CustomUser(AbstractUser):
    is_admin = models.BooleanField(default=False)


class Package(models.Model):
    name = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    itinerary = models.JSONField(help_text="Day-by-day itinerary plan (e.g., [{'day': 1, 'places': ['Place 1', 'Place 2']}, ...])")
    duration = models.IntegerField(help_text="Duration in days")
    price_per_person = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='packages/', null=True, blank=True)
    available_dates = models.JSONField(help_text="List of available dates for booking. Example: [{'start_date': '2025-04-20', 'end_date': '2025-04-25'}, ...]")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Travel Package'
        verbose_name_plural = 'Travel Packages'


class Booking(models.Model):
    STATUS_CHOICES = [
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    package = models.ForeignKey('Package', on_delete=models.CASCADE)
    num_travelers = models.IntegerField()
    preferred_date = models.DateField(default=timezone.now)
    contact_info = models.CharField(max_length=255)
    payment_screenshot = models.ImageField(upload_to='payment_proofs/', null=True, blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_verified = models.BooleanField(default=False)
    booked_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Confirmed')

    def __str__(self):
        return f'Booking for {self.user.username} - {self.package.name}'

    def save(self, *args, **kwargs):
        # Calculate the total price based on package price and number of travelers
        self.total_price = self.package.price_per_person * self.num_travelers
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'


class Review(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    package = models.ForeignKey('Package', on_delete=models.CASCADE)
    rating = models.IntegerField(default=5)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.username} on {self.package.name}"

    def clean(self):
        if not (1 <= self.rating <= 5):
            raise ValidationError('Rating must be between 1 and 5.')


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'content']
        widgets = {
            'content': forms.Textarea(attrs={
                'placeholder': 'Write your review here...',
                'rows': 4
            }),
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5}),
        }


class PaymentProof(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    message = models.TextField(blank=True, null=True)
    screenshot = models.FileField(upload_to='payment_proofs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.email} - Verified: {self.is_verified}"

    def save(self, *args, **kwargs):
        # Check if is_verified is changing to True, then send verification email
        if self.pk:
            old = PaymentProof.objects.get(pk=self.pk)
            if not old.is_verified and self.is_verified:
                self.send_verification_email()
        super().save(*args, **kwargs)

    def send_verification_email(self):
        subject = "🎟️ Payment Proof Verified – Trivishna"
        message = f"""
Dear {self.email},

We are pleased to inform you that your payment proof for the booking with Trivishna has been successfully verified!

Booking Details:
- Booking ID: {self.booking.id}
- Destination: {self.booking.package.name}
- Travel Date: {self.booking.preferred_date}

We appreciate you choosing Trivishna for your travel experience. Your payment has been successfully processed, and we are now proceeding with your booking.

You can view the details of your booking on your dashboard at any time.

If you have any questions or concerns, feel free to reach out to us at trivishnahelp@gmail.com

Thank you for trusting Trivishna for your travel plans.

Safe travels,  
The Trivishna Team
        """
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.email],
            fail_silently=False,
        )

# models.py
class CartItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    number_of_travelers = models.PositiveIntegerField(default=1)  # Number of travelers for each package

    @property
    def total_price(self):
        return self.package.price_per_person * self.number_of_travelers

    def __str__(self):
        return f"{self.package.name} - {self.number_of_travelers} travelers"