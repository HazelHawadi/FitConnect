from django.shortcuts import render, get_object_or_404, redirect
from .models import Program, AvailableDate, Booking, Review
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from .forms import ReviewForm


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
def book_program(request, pk):
    program = get_object_or_404(Program, pk=pk)
    available_dates = AvailableDate.objects.filter(program=program, is_booked=False)

    if request.method == 'POST':
        date_id = request.POST.get('date')
        sessions = int(request.POST.get('sessions'))
        selected_date = get_object_or_404(AvailableDate, id=date_id)

        total_cost = sessions * program.price_per_session

        request.session['booking_data'] = {
            'program_id': program.id,
            'date_id': selected_date.id,
            'sessions': sessions,
            'total_cost': float(total_cost),
        }

        return redirect('confirm_booking')

    return render(request, 'programs/book_program.html', {
        'program': program,
        'available_dates': available_dates,
    })


@login_required
def add_review(request, program_id):
    program = get_object_or_404(Program, pk=program_id)

    # Check if user has booked the program
    if not Booking.objects.filter(user=request.user, program=program).exists():
        return redirect('program_detail', program_id=program.id)

    # One review per user
    review, created = Review.objects.get_or_create(user=request.user, program=program)
    form = ReviewForm(request.POST or None, instance=review)

    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('program_detail', program_id=program.id)

    return render(request, 'programs/review_form.html', {'form': form, 'program': program})

@login_required
def delete_review(request, program_id):
    review = get_object_or_404(Review, program_id=program_id, user=request.user)
    if request.method == 'POST':
        review.delete()
        return redirect('program_detail', program_id=program_id)
    return render(request, 'programs/confirm_delete_review.html', {'review': review})


def confirm_booking(request, program_id):
    if request.method == 'POST':
        program = get_object_or_404(Program, pk=program_id)
        date_id = request.POST.get('date')
        sessions = int(request.POST.get('sessions', 1))
        date = get_object_or_404(AvailableDate, pk=date_id)

        total = sessions * program.price_per_session

        request.session['booking_data'] = {
            'program_id': program.id,
            'date_id': date.id,
            'sessions': sessions,
            'total': float(total),
        }

        context = {
            'program': program,
            'date': date,
            'sessions': sessions,
            'total': total,
        }
        return render(request, 'programs/confirm_booking.html', context)
    return redirect('home')
