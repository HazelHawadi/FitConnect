from django.shortcuts import render, get_object_or_404, redirect
from .models import Program, SessionBooking
from .forms import SessionBookingForm


def program_detail(request, program_id):
    program = get_object_or_404(Program, id=program_id)
    form = SessionBookingForm()

    if request.method == 'POST':
        form = SessionBookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.program = program
            booking.save()
            return redirect('booking_success')

    return render(request, 'bookings/program_detail.html', {
        'program': program,
        'form': form,
    })


def booking_success(request):
    return render(request, 'bookings/booking_success.html')
