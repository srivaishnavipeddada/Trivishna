import requests
from django.conf import settings
from django.core.mail import send_mail

GOOGLE_API_KEY = settings.GOOGLE_API_KEY  # Make sure this is set in settings.py

# Trip Planner - Get top tourist places using Google Places API
def get_top_places(destination, num_places=10):
    search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    
    params = {
        "query": f"top tourist attractions in {destination}",
        "key": GOOGLE_API_KEY,
    }

    response = requests.get(search_url, params=params)
    data = response.json()

    places = []
    if data.get("results"):
        for place in data["results"][:num_places]:
            name = place.get("name")
            if name:
                places.append(name)
    
    return places

# Booking Email Notification
def send_booking_email_to_admin(booking):
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
