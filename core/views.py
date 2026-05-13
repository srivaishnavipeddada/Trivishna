import json
import requests
from datetime import datetime
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.core.files.storage import FileSystemStorage
from django.db.models import Avg
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from .utils import get_top_places, send_booking_email_to_admin

from .forms import CustomUserCreationForm, BookingForm, ReviewForm, PaymentProofForm
from .models import Package, Booking, Review, PaymentProof

import openai
openai.api_key = settings.OPENAI_API_KEY

User = get_user_model()

# ---------- Utility ----------
def is_admin(user):
    return user.is_staff

def get_top_places(destination, num_places):
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        'query': f'tourist attractions in {destination}',
        'key': settings.GOOGLE_API_KEY,
    }
    response = requests.get(url, params=params)
    data = response.json()

    if data.get('status') != 'OK':
        return []

    results = data.get('results', [])[:num_places]
    return [place['name'] for place in results]

# ---------- Auth ----------
def signup_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password1']
        confirm_password = request.POST['password2']

        if password == confirm_password:
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already taken.')
            elif User.objects.filter(email=email).exists():
                messages.error(request, 'Email already in use.')
            else:
                try:
                    user = User.objects.create_user(username=username, email=email, password=password)
                    messages.success(request, 'Account created! Please log in.')
                    return redirect('login')
                except Exception as e:
                    messages.error(request, f'Error creating account: {str(e)}')
        else:
            messages.error(request, 'Passwords do not match.')

    return render(request, 'core/signup.html')

def login_view(request):
    # Check if the user is already logged in
    if request.user.is_authenticated:
        return redirect('home')  # Redirect to home if the user is already logged in
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            # Authenticate and log the user in
            user = form.get_user()
            login(request, user)
            
            # Get the next URL if available, else redirect to home
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        else:
            # Display an error message if the credentials are invalid
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        # Initialize the form when it's a GET request
        form = AuthenticationForm()

    # Render the login template
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

# ---------- Home & Dashboard ----------
def home(request):
    packages = Package.objects.all()[:6]
    reviews = Review.objects.all()[:3]
    return render(request, 'base.html', {'packages': packages, 'reviews': reviews})

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_dashboard(request):
    context = {
        'total_packages': Package.objects.count(),
        'total_bookings': Booking.objects.count(),
        'total_users': User.objects.filter(is_staff=False).count(),
        'recent_bookings': Booking.objects.select_related('user', 'package').order_by('-booked_at')[:5],
    }
    return render(request, 'core/admin_dashboard.html', context)

from django.core.mail import send_mail
def send_booking_notification_email(booking):
    subject = 'New Booking Notification'
    from_email = 'vouchsurehelp@gmail.com'
    to_email = ['vouchsurehelp@gmail.com']

    message = f"""
    New Booking Notification:

    Package: {booking.package.name}
    User: {booking.user.username}
    Email: {booking.user.email}
    Booking Date: {booking.booked_at}
    Preferred Travel Date: {booking.preferred_date}
    Contact Info: {booking.contact_info}
    Total Price: ₹{booking.total_price}
    """

    send_mail(subject, message, from_email, to_email)


# ---------- Package Views ----------
@login_required
def package_list(request):
    packages = Package.objects.all()

    search_query = request.GET.get('search')
    duration = request.GET.get('duration')
    sort = request.GET.get('sort')

    if search_query:
        packages = packages.filter(destination__icontains=search_query)

    if duration:
        try:
            packages = packages.filter(duration__lte=int(duration))
        except ValueError:
            pass

    if sort == 'asc':
        packages = packages.order_by('price_per_person')
    elif sort == 'desc':
        packages = packages.order_by('-price_per_person')

    return render(request, 'core/package_list.html', {'packages': packages})

@login_required
def package_detail(request, package_id):
    package = get_object_or_404(Package, id=package_id)
    reviews = Review.objects.filter(package=package)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            # Save the review
            review = form.save(commit=False)
            review.package = package
            review.user = request.user
            review.save()
            return redirect('package_detail', package_id=package.id)
    else:
        form = ReviewForm()

    return render(request, 'package_detail.html', {
        'package': package,
        'form': form,
        'reviews': reviews,
    })
from .utils import send_booking_email_to_admin
# ---------- Booking ----------
@login_required
def book_package(request, package_id):
    package = get_object_or_404(Package, id=package_id)

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.package = package
            booking.user = request.user
            booking.save()

            # Send email to admin
            send_booking_email_to_admin(booking)

            # Save booking ID in session for use in payment view
            request.session['booking_id'] = booking.id

            # Redirect to payment page (no kwargs)
            return redirect('payment')

    else:
        form = BookingForm()

    return render(request, 'core/book_package.html', {'form': form, 'package': package})

@login_required
def payment_view(request):
    booking_ids = request.session.get('booking_ids', [])
    total_amount = request.session.get('total_price', 0)

    if not booking_ids:
        messages.error(request, "No bookings found.")
        return redirect('home')

    bookings = Booking.objects.filter(id__in=booking_ids, user=request.user)

    if request.method == 'POST':
        posted_ids = request.POST.getlist('booking_ids')  # Comes from form as list of hidden inputs

        # Make sure the posted IDs match session's booking_ids for security
        if set(map(str, booking_ids)) == set(posted_ids):
            # Mark all bookings as Paid
            bookings.update(status='Paid')
            messages.success(request, "Payment successful for all items! 🎉")

            # Clear payment session
            del request.session['booking_ids']
            del request.session['total_price']

            return redirect('core:success_view')

    return render(request, 'core/payment.html', {
        'bookings': bookings,
        'total_amount': total_amount
    })




@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-booked_at')
    return render(request, 'core/my_bookings.html', {'bookings': bookings})

@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    if booking.status != "Canceled":
        booking.status = "Canceled"
        booking.save()
        messages.success(request, "Booking canceled.")
    else:
        messages.info(request, "Already canceled.")
    return redirect('my_bookings')

# ---------- Payment Proof ----------
def upload_payment_proof(request, booking_id):
    if request.method == 'POST' and request.FILES.get('screenshot'):
        screenshot = request.FILES['screenshot']
        phone = request.POST['phone']
        email = request.POST['email']
        message = request.POST.get('message', '')

        try:
            # Find the booking using the booking_id (not just phone/email)
            booking = Booking.objects.get(id=booking_id)

            # Create the PaymentProof and link it to the booking
            proof = PaymentProof.objects.create(
                booking=booking,  # Link the proof to the booking
                phone=phone,
                email=email,
                message=message,
                screenshot=screenshot
            )

            # Optionally, update the booking's payment screenshot
            booking.payment_screenshot = screenshot
            booking.save()

            # Send email notification to the user (payment proof uploaded)
            send_mail(
                'Payment Proof Uploaded Successfully',
                f'Hello,\n\nYour payment proof for booking ID {booking_id} has been uploaded successfully.\n\nThank you for using Trivishna!',
                settings.DEFAULT_FROM_EMAIL,  # Sender's email
                [email],  # Recipient's email (user who uploaded the proof)
                fail_silently=False,
            )

            # Success message for the view
            messages.success(request, "Payment proof linked and email notification sent successfully!")

        except Booking.DoesNotExist:
            messages.warning(request, "Payment saved, but no matching booking found.")

        return redirect('success_view')  # redirect to a success page or wherever

    return render(request, 'core/upload_payment_proof.html')

def success_view(request):
    return render(request, 'success.html')

# ---------- Trip Planner ----------
@login_required
def generate_trip_plan(request, package_id):
    package = get_object_or_404(Package, id=package_id)

    if request.method == "POST":
        start_date_str = request.POST.get("start_date")
        duration = int(request.POST.get("duration", 0))
        if duration <= 0:
            messages.error(request, "Invalid duration.")
            return redirect('package_detail', package_id=package_id)

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid date format.")
            return redirect('package_detail', package_id=package_id)

        attractions = get_top_places(package.destination, duration * 2)
        itinerary = {f"Day {i+1}": attractions[i*2:i*2+2] or ["Explore at leisure"] for i in range(duration)}

        return render(request, "core/trip_plan_result.html", {
            "package": package,
            "itinerary": itinerary,
            "start_date": start_date,
            "duration": duration,
        })

    return render(request, "core/trip_plan.html", {"package": package})

# ---------- Chatbot ----------
@csrf_exempt
def chatbot_response(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_message = data.get('message', '').lower()

        if any(word in user_message for word in ['travel package', 'trip', 'vacation']):
            return JsonResponse({'response': 'Here are some popular packages: Mystic Manali Retreat, Jaipur Heritage Tour, Andaman Island Explorer.'})
        return JsonResponse({'response': "I didn't catch that. Can you rephrase?"})
from django.core.mail import send_mail

@csrf_exempt
def chatbot_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message')
            if not user_message:
                return JsonResponse({'message': 'Please provide a message'}, status=400)

            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=user_message,
                max_tokens=150
            )
            return JsonResponse({'message': response.choices[0].text.strip()})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'message': 'Invalid request method'}, status=400)

def chatbot_view(request):
    return render(request, 'core/chatbot.html')

def review_success(request):
    return render(request, 'core/review_success.html')

def send_verification_email(proof):
    subject = "🎟️ Payment Proof Verified – Trivishna"
    
    message = f"""
    Dear {proof.email},

    We are pleased to inform you that your payment proof for the booking with Trivishna has been successfully verified!

    **Booking Details:**
    - **Booking ID:** {proof.booking.id}
    - **Destination:** {proof.booking.package.name} 
    - **Travel Dates:** {proof.booking.start_date} to {proof.booking.end_date}
    
    We appreciate you choosing Trivishna for your travel experience. Your payment has been successfully processed, and we are now proceeding with your booking.

    You can view the details of your booking on your dashboard at any time.

    If you have any questions or concerns, feel free to reach out to us at support@trivishna.com.

    Thank you for trusting Trivishna for your travel plans.

    Safe travels,
    The Trivishna Team
    """

    # Send email
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[proof.email],
        fail_silently=False,
    )
from django.http import HttpResponseRedirect
from django.urls import reverse
def add_to_cart(request, package_id):
    package = get_object_or_404(Package, id=package_id)
    quantity = int(request.POST.get('quantity', 1))  # Default to 1 if not provided

    # Convert price from Decimal to float
    price = float(package.price_per_person)

    # Retrieve the cart from the session
    cart = request.session.get('cart', [])

    # Check if the package already exists in the cart
    existing_package = next((item for item in cart if item['id'] == package.id), None)

    if existing_package:
        # Update quantity if the package already exists in the cart
        existing_package['quantity'] += quantity
    else:
        # Add new package to the cart
        cart.append({
            'id': package.id,
            'name': package.name,
            'price': price,  # Store the price as a float
            'quantity': quantity,
        })

    # Save the cart back to the session
    request.session['cart'] = cart

    # Return a JsonResponse with success message
    return JsonResponse({
        'success': True,
        'message': f"{package.name} added to your cart!",
        'cart_item_count': len(cart),
    })


from decimal import Decimal

def view_cart(request):
    cart = request.session.get('cart', [])
    
    # Ensure consistent data type (Decimal) for price calculation
    total_price = sum(Decimal(item['price']) * Decimal(item['quantity']) for item in cart)

    context = {
        'cart': cart,
        'total_price': total_price
    }
    return render(request, 'core/view_cart.html', context)




def remove_from_cart(request, package_id):
    cart = request.session.get('cart', [])
    cart = [item for item in cart if item['id'] != package_id]
    request.session['cart'] = cart
    return redirect('view_cart')



@login_required
def checkout(request):
    cart = request.session.get('cart', [])

    # Validate each cart item
    valid_cart = []
    for item in cart:
        try:
            item['price'] = float(item['price'])  # Ensure it's a float
            item['total'] = item['price'] * item['quantity']
            valid_cart.append(item)
        except (KeyError, ValueError, TypeError):
            continue  # Skip invalid items

    if not valid_cart:
        messages.error(request, "Your cart is empty.")
        return redirect('home')

    total_price = sum(item['total'] for item in valid_cart)

    if request.method == "POST":
        preferred_date = request.POST.get('preferred_date')
        contact_info = request.POST.get('contact_info')

        bookings = []  # Store all booking objects
        for item in valid_cart:
            package = Package.objects.get(id=item['id'])
            booking = Booking.objects.create(
                user=request.user,
                package=package,
                num_travelers=item['quantity'],
                total_price=item['total'],
                preferred_date=preferred_date,
                contact_info=contact_info,
            )
            bookings.append(booking)

        # Clear the cart after booking
        request.session['cart'] = []

        # Pass the list of booking IDs to the payment page
        request.session['booking_ids'] = [b.id for b in bookings]
        request.session['total_price'] = total_price  # Save total to session for payment

        return redirect('payment')  # no booking_id now, we’re sending all

    return render(request, 'core/checkout.html', {
        'cart_items': valid_cart,
        'total_price': total_price
    })

def send_cart_abandonment_email(user_email, cart_details):
    subject = "🌞 Your Dream Vacation Awaits – Complete Your Booking!"
    message = f"Hey, your cart is still waiting for you! Complete your booking today for exclusive offers! Here's what you left behind:\n\n{cart_details}"
    
    # Send the email
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user_email],
        fail_silently=False,
    )



# Remove the duplicate function definition below.
def booking_confirmation(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    return render(request, 'core/booking_confirmation.html', {'booking': booking})


def cancel_booking(request, booking_id):
    booking = Booking.objects.get(id=booking_id)

    # Assuming you set the status to "Cancelled" when the booking is canceled
    booking.status = 'Cancelled'
    booking.save()

    # Redirect back to the user's bookings page
    return redirect('my_bookings')

from django.shortcuts import render, get_object_or_404

def booking_confirmation(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    return render(request, 'core/booking_confirmation.html', {'booking': booking})