import stripe
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
    program = get_object_or_404(Program, pk=program_id)

    if request.method == 'POST':
        form = BookingForm(request.POST, program=program)
        if form.is_valid():
            request.session['booking_data'] = {
                'program_id': program_id,
                'date_id': form.cleaned_data['date'].id,
                'sessions': form.cleaned_data['sessions'],
            }
            return redirect('confirm_booking')
    else:
        form = BookingForm(program=program)

    return render(request, 'programs/booking_form.html', {'form': form, 'program': program})


@csrf_exempt
def create_checkout_session(request):
    if request.method == 'POST':
        amount = request.POST.get('amount')

        if not amount:
            raise ValueError("Amount is missing")

        try:
            amount = float(amount)
        except ValueError:
            raise ValueError("Invalid amount format")

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': 'Program Booking',
                        },
                        'unit_amount': int(amount * 100),
                    },
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=request.build_absolute_uri('/success/'),
            cancel_url=request.build_absolute_uri('/cancel/'),
        )

        return JsonResponse({
            'id': session.id
        })
        
        
def confirm_booking(request):
    booking_data = request.session.get('booking_data')
    if not booking_data:
        return redirect('home')

    program = get_object_or_404(Program, pk=booking_data['program_id'])
    date = program.dates.get(id=booking_data['date_id'])
    sessions = booking_data['sessions']
    total = float(program.price_per_session) * sessions

    if request.method == 'POST':
        # create Stripe Checkout Session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f"{program.title} on {date.date}",
                    },
                    'unit_amount': int(total * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.build_absolute_uri('/booking/success/'),
            cancel_url=request.build_absolute_uri('/programs/'),
        )
        return redirect(checkout_session.url, code=303)

    return render(request, 'programs/confirm_booking.html', {
        'program': program,
        'date': date,
        'sessions': sessions,
        'total': total,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY
    })
    
    
def booking_success(request):
    booking_data = request.session.pop('booking_data', None)
    if not booking_data:
        return redirect('home')

    program = get_object_or_404(Program, pk=booking_data['program_id'])
    date = program.dates.get(id=booking_data['date_id'])
    sessions = booking_data['sessions']
    total_cost = float(program.price_per_session) * sessions

    booking = Booking.objects.create(
        user=request.user,
        program=program,
        date=date,
        sessions=sessions,
        total_cost=total_cost,
        paid=True
    )

    return render(request, 'programs/booking_success.html', {
        'booking': booking
    })



@login_required
def add_review(request, program_id):
    program = get_object_or_404(Program, pk=program_id)

    existing_review = Review.objects.filter(user=request.user, program=program).first()

    if existing_review:
        if request.method == 'POST':
            existing_review.rating = request.POST.get('rating')
            existing_review.comment = request.POST.get('comment')
            existing_review.save()
            return redirect('program_detail', program_id=program.id)
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
        return redirect('program_detail', program_id=program_id)
    return render(request, 'programs/confirm_delete_review.html', {'review': review})


def program_list(request):
    programs = Program.objects.all()
    return render(request, 'programs/program_list.html', {'programs': programs})
