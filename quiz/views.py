from django.shortcuts import render, render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required


@login_required(login_url="/login/")
def index(request):
    context = {}
    return render(request, 'quiz/index.html', context=context)

# Create your views here.
def post(request):
    return
