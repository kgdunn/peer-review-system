from django.shortcuts import render
from django.http import HttpResponse

def display_grades(request):
    """
    Displays the grades to the student here.
    """
    return HttpResponse('Your grades will be shown here.')
