from django.shortcuts import render
from programs.models import Program


def home(request):
    programs = Program.objects.all()
    return render(request, 'home/index.html', {'programs': programs})