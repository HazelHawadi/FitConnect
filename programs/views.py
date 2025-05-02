from django.shortcuts import render, get_object_or_404, redirect
from .models import Program, AvailableDate, Booking
from django.contrib.auth.decorators import login_required

def program_list(request):
    programs = Program.objects.all()
    return render(request, 'programs/program_list.html', {'programs': programs})

def program_detail(request, pk):
    program = get_object_or_404(Program, pk=pk)
    available_dates = program.dates.filter(is_booked=False)
    return render(request, 'programs/program_detail.html', {
        'program': program,
        'available_dates': available_dates,
    })

@login_required
def book_program(request, pk):
    program = get_object_or_404(Program, pk=pk)

    if request.method == 'POST':
        date_id = request.POST.get('date')
        sessions = int(request.POST.get('sessions', 1))
        selected_date = get_object_or_404(AvailableDate, pk=date_id)

        total = sessions * float(program.price_per_session)

        booking = Booking.objects.create(
            user=request.user,
            program=program,
            date=selected_date,
            sessions=sessions,
            total_cost=total,
        )

        selected_date.is_booked = True
        selected_date.save()

        # Redirect to payment page (to be implemented with Stripe)
        return redirect('stripe_checkout', booking_id=booking.id)

    return redirect('program_detail', pk=pk)
