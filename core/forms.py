from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import Booking, Review, PaymentProof

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['preferred_date', 'num_travelers']
        widgets = {
            'preferred_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'num_travelers': forms.NumberInput(attrs={'class': 'form-input'}),
            
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'content']
        widgets = {
            'rating': forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'max': 5}),
            'content': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
        }


class PaymentProofForm(forms.ModelForm):
    class Meta:
        model = PaymentProof
        fields = ['phone', 'email', 'message', 'screenshot']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'message': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
            'screenshot': forms.ClearableFileInput(attrs={'class': 'form-file'}),
        }
