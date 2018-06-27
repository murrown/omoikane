from django.shortcuts import render, render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from .models import QuizList, UserExpression
import urllib


@login_required(login_url="/login/")
def index(request):
    context = {}
    return render(request, "quiz/index.html", context=context)

def lists(request):
    response = JsonResponse({"results": list(
        QuizList.objects.order_by("name").values("id", "name"))}, safe=False)
    return response

def due(request):
    user = request.user
    _, quizlist_id = request.body.decode().split('=')
    quizlist = QuizList.objects.get(id=int(quizlist_id))
    due_exs = UserExpression.get_due_expressions(user=user, quizlist=quizlist)
    response = JsonResponse({"results": [uex.quiz_dict for uex in due_exs]})
    return response

def user_expression_from_request(request):
    user = request.user
    _, expression_text = request.body.decode().split('=')
    expression_text = urllib.parse.unquote_plus(expression_text)
    return UserExpression.objects.get(
        user=user, expression__text=expression_text)

def success(request):
    return HttpResponse(user_expression_from_request(request).succeed())

def failure(request):
    return HttpResponse(user_expression_from_request(request).fail())
