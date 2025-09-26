import stripe
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from .models import Program, AvailableDate, Booking, Review
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from .forms import ReviewForm, BookingForm
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView
from .models import Instructor
from datetime import datetime, time as dt_time
from django.contrib import messages


stripe.api_key = settings.STRIPE_SECRET_KEY


class InstructorListView(ListView):
    model = Instructor
    template_name = 'programs/instructor_list.html'
    context_object_name = 'instructors'
    
    
class InstructorDetailView(DetailView):
    model = Instructor
    template_name = 'programs/instructor_detail.html'
    context_object_name = 'instructor'


def program_list(request):
    programs = Program.objects.all()
    return render(request, 'programs/program_list.html', {'programs': programs})


def program_detail(request, pk):
    program = get_object_or_404(Program, pk=pk)
    available_dates = AvailableDate.objects.filter(program=program, is_booked=False)

    user_has_reviewed = False
    if request.user.is_authenticated:
        user_has_reviewed = Review.objects.filter(user=request.user, program=program).exists()

    return render(request, 'programs/program_detail.html', {
        'program': program,
        'available_dates': available_dates,
        'user_has_reviewed': user_has_reviewed,
    })


@login_required
def book_program(request, program_id):
    program = Program.objects.get(pk=program_id)

    if request.method == 'POST':
        form = BookingForm(request.POST, program=program)
        if form.is_valid():
            booking_dt = form.cleaned_data['booking_datetime']
            sessions = form.cleaned_data['sessions']

            # Save AvailableDate entry or mark as booked
            available_date, created = AvailableDate.objects.get_or_create(
                program=program,
                date=booking_dt.date(),
                time=booking_dt.time()
            )
            available_date.is_booked = True
            available_date.save()

            total_cost = program.price_per_session * sessions

            booking = Booking.objects.create(
                user=request.user,
                program=program,
                date=available_date,
                time=booking_dt.time(),
                sessions=sessions,
                total_cost=total_cost,
                paid=False
            )

            return redirect('confirm_booking', booking_id=booking.id)

    else:
        form = BookingForm(program=program)

    return render(request, 'programs/booking_form.html', {'form': form, 'program': program})


@require_POST
def create_checkout_session(request, program_id):
    program = get_object_or_404(Program, id=program_id)
    total = request.POST.get('total')  # Retrieve total from POST data

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f"{program.title}",
                    },
                    'unit_amount': int(float(total) * 100),  # Convert total to cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.build_absolute_uri('/booking/success/'),
            cancel_url=request.build_absolute_uri('/programs/'),
        )

        return JsonResponse({'id': checkout_session.id})

    except Exception as e:
        return JsonResponse({'error': str(e)})
        
        
@login_required
def confirm_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    program = booking.program
    date = booking.date
    sessions = booking.sessions
    total = booking.total_cost

    if request.method == 'POST':
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {'name': f"{program.title} on {date.date}"},
                        'unit_amount': int(total * 100),
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=request.build_absolute_uri(
                    f"/programs/booking/success/?booking_id={booking.id}"
                ),
                cancel_url=request.build_absolute_uri(f"/programs/confirm-booking/{booking.id}/"),
            )
            return redirect(checkout_session.url, code=303)
        except Exception as e:
            messages.error(request, f"Stripe error: {e}")
            return redirect('confirm_booking', booking_id=booking.id)

    return render(request, 'programs/confirm_booking.html', {
        'booking': booking,
        'program': program,
        'date': date,
        'sessions': sessions,
        'total': total,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
    })
    

@require_POST
def complete_booking(request):
    # Get form data and create a booking
    Booking.objects.create(
        full_name=request.POST['full_name'],
        email=request.POST['email'],
        phone_number=request.POST['phone_number'],
    )
    return render(request, 'booking_success.html')

    
@require_POST
def cache_booking_data(request):
    try:
        client_secret = request.POST.get('client_secret')
        save_info = request.POST.get('save_info')

        request.session['save_info'] = save_info

        return HttpResponse(status=200)
    except Exception as e:
        return HttpResponse(content=e, status=400)
    

@login_required
def booking_success(request):
    booking_id = request.GET.get('booking_id')
    if not booking_id:
        messages.error(request, "Booking not found.")
        return redirect('program_list')

    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    # Mark booking as paid
    if not booking.paid:
        booking.paid = True
        booking.save()

    return render(request, 'programs/booking_success.html', {'booking': booking})


def payment_success(request):
    program_id = request.GET.get('program_id')
    program = get_object_or_404(Program, id=program_id)

    date = AvailableDate.objects.filter(program=program).first()
    total = program.price_per_session

    return render(request, 'payment_success.html', {
        'program': program,
        'date': date,
        'total': total
    })

def payment_cancel(request):
    program_id = request.GET.get('program_id')
    program = get_object_or_404(Program, id=program_id)

    return render(request, 'payment_cancel.html', {
        'program': program
    })


@login_required
def my_bookings(request):
    user = request.user
    bookings = user.bookings.all()

    return render(request, 'programs/my_bookings.html', {'bookings': bookings})


@login_required
def update_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    if request.method == 'POST':
        form = BookingForm(request.POST, program=booking.program)
        if form.is_valid():
            booking_dt = form.cleaned_data['booking_datetime']
            sessions = form.cleaned_data['sessions']

            # Free up the old slot
            if booking.date:
                booking.date.is_booked = False
                booking.date.save()

            # Assign the new slot
            available_date, created = AvailableDate.objects.get_or_create(
                program=booking.program,
                date=booking_dt.date(),
                time=booking_dt.time()
            )
            available_date.is_booked = True
            available_date.save()

            booking.date = available_date
            booking.time = booking_dt.time()

            if not booking.paid:
                booking.sessions = sessions
                booking.total_cost = booking.program.price_per_session * sessions

            booking.save()
            messages.success(request, "Booking updated successfully!")
            return redirect('my_bookings')
    else:
        form = BookingForm(
            initial={
                'booking_datetime': datetime.combine(booking.date.date, booking.time),
                'sessions': booking.sessions,
            },
            program=booking.program
        )

    available_dates = AvailableDate.objects.filter(program=booking.program).exclude(
        id=booking.date.id
    )

    return render(request, 'programs/update_booking.html', {
        'form': form,
        'booking': booking,
        'available_dates': available_dates,
    })


@login_required
def delete_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    if request.method == 'POST':
        booking.delete()
        messages.success(request, "Booking deleted successfully.")
        return redirect('my_bookings')

    return render(request, 'programs/confirm_delete_booking.html', {'booking': booking})


@login_required
def add_review(request, program_id):
    program = get_object_or_404(Program, pk=program_id)

    existing_review = Review.objects.filter(user=request.user, program=program).first()

    if existing_review:
        if request.method == 'POST':
            existing_review.rating = request.POST.get('rating')
            existing_review.comment = request.POST.get('comment')
            existing_review.save()
            return redirect('program_detail', pk=program.id)
        else:
            return render(request, 'programs/add_review.html', {'review': existing_review, 'program': program})

    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        if rating and comment:
            review = Review(user=request.user, program=program, rating=rating, comment=comment)
            review.save()
            return redirect('program_detail', pk=program.id)

    return render(request, 'programs/add_review.html', {'program': program})


@login_required
def delete_review(request, program_id):
    review = get_object_or_404(Review, program_id=program_id, user=request.user)
    if request.method == 'POST':
        review.delete()
        return redirect('program_detail', pk=program_id)
    return render(request, 'programs/confirm_delete_review.html', {'review': review})


@login_required
def edit_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    if request.method == 'POST':
        review.rating = request.POST.get('rating')
        review.comment = request.POST.get('comment')
        review.save()
        messages.success(request, "Your review was updated successfully.")
        return redirect('program_detail', pk=review.program.id)
    
    return render(request, 'programs/add_review.html', {
        'review': review,
        'program': review.program
    })


def program_list(request):
    programs = Program.objects.all()
    return render(request, 'programs/program_list.html', {'programs': programs})
