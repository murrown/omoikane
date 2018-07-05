from django.shortcuts import render, render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from .models import QuizList, QuizListItem, Expression, UserExpression
from .user_models import utcnow
import urllib


GUEST_USER, _ = User.objects.get_or_create(username="guest")


def index(request):
    context = {}
    return render(request, "quiz/index.html", context=context)


def lists(request):
    results = []
    now = utcnow()
    user = request.user
    if user.is_anonymous:
        user = GUEST_USER
    uexs = (UserExpression.objects.filter(user=user)
                                  .select_related("expression"))
    done_exs = set([uex.expression.id for uex in uexs if uex.due > now])
    all_exs = set([uex.expression.id for uex in uexs])
    for ql in QuizList.objects.order_by("name").all():
        items = set(QuizListItem.objects
            .filter(quizlist=ql).values_list("expression", flat=True))
        tried_items = items & all_exs
        done_items = items & done_exs
        results.append({"id": ql.id, "name": ql.name, "done": len(done_items),
                        "tried": len(tried_items), "total": len(items)})
    response = JsonResponse({"results": results}, safe=False)
    return response


def due(request):
    user = request.user
    if user.is_anonymous:
        user = GUEST_USER
    _, quizlist_id = request.body.decode().split('=')
    quizlist = QuizList.objects.get(id=int(quizlist_id))
    due_exs = UserExpression.get_due_expressions(user=user, quizlist=quizlist)
    response = JsonResponse({"results": [uex.quiz_dict for uex in due_exs]})
    return response


def user_expression_from_request(request):
    user = request.user
    if user.is_anonymous:
        user = GUEST_USER
    _, expression_text = request.body.decode().split('=')
    expression_text = urllib.parse.unquote_plus(expression_text)
    try:
        return UserExpression.objects.get(
            user=user, expression__text=expression_text)
    except UserExpression.DoesNotExist:
        e = Expression.objects.get(text=expression_text)
        ue = UserExpression.objects.create(user=user, expression=e)
        return ue


def success(request):
    return HttpResponse(user_expression_from_request(request).succeed())


def failure(request):
    return HttpResponse(user_expression_from_request(request).fail())
