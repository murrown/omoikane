from django.db import models
from django.db.models.query import QuerySet
from django.contrib.auth.models import User

from datetime import datetime, timedelta
from pytz import utc
import romkan
from .definition_models import Association, Expression
from .list_models import QuizList


ONE_MINUTE = 60
ONE_HOUR = 60 * ONE_MINUTE
ONE_DAY = 24 * ONE_HOUR
DEFAULT_INTERVAL = 2 * ONE_MINUTE

MULTIPLIER = 2


def utcnow():
    return datetime.utcnow().replace(tzinfo=utc)


class UserExpression(models.Model):
    user = models.ForeignKey(User, null=False, db_index=True)
    expression = models.ForeignKey(Expression, null=False, db_index=True)
    modified = models.DateTimeField(auto_now=True)
    due = models.DateTimeField(default=utcnow)
    interval = models.IntegerField(default=0, null=False)

    class Meta:
        unique_together = ("user", "expression")
        index_together = [("user", "expression")]

    @classmethod
    def get_due_expressions(cls, user, quizlist=None):
        now = utcnow()
        due_uexs = UserExpression.objects.filter(user=user, due__lt=now)
        if quizlist is not None:
            if isinstance(quizlist, int):
                quizlist = QuizList.objects.get(id=quizlist)
            list_expressions = quizlist.expressions
            due_uexs = due_uexs.filter(expression__text__in=list_expressions)

            if due_uexs.count() <= 1:
                list_expressions = [ex for ex in list_expressions
                    if ex not in UserExpression.objects.filter(user=user)
                    .values_list("expression__text", flat=True)]
                if list_expressions:
                    uex = UserExpression.objects.create(
                        user=user, expression=Expression.objects.get(
                            text=list_expressions[0]))
                    due_uexs = [uex]

        if isinstance(due_uexs, QuerySet):
            due_uexs = [uex for uex in due_uexs]

        return due_uexs

    @property
    def quiz_dict(self):
        ex = self.expression
        assocs, readings = ex.get_summary_data()
        for r in list(readings):
            romr = romkan.to_roma(r)
            readings.append(romr)
            if "nn" in romr:
                readings.append(romr.replace("nn", "n"))
        rdict = {"expression": ex.text,
                 "readings": readings,
                 "associations": [{"sense": a.sense, "reading": a.reading}
                                  for a in assocs],
                 "audio": ex.audio if ex.audio else "",
                }
        return rdict

    def succeed(self):
        now = utcnow()
        # self.interval basically holds the previous successful interval
        # self.due is always a little more than self.modified + self.interval
        self.interval = max(DEFAULT_INTERVAL, self.interval,
                            (now - self.modified).total_seconds())
        due = now + timedelta(0, self.interval * MULTIPLIER)
        new_interval = due - now
        if self.interval and new_interval < timedelta(0, self.interval):
            raise Exception("Bad interval.")
        self.due = due
        UserGuess.objects.create(user_expression=self, success=True)
        self.save()

    def fail(self):
        self.interval = DEFAULT_INTERVAL
        self.due = utcnow()
        UserGuess.objects.create(user_expression=self, success=False)
        self.save()

    def verify_reading(self, guess, readings=None):
        guess = romkan.to_roma(romkan.to_kana(guess.replace(' ', '')))
        if not readings:
            readings = set(Association.objects
                           .filter(expression=self.expression)
                           .values_list('reading', flat=True))
        readings = map(romkan.to_roma, readings)
        return guess in readings


class UserGuess(models.Model):
    user_expression = models.ForeignKey(
        UserExpression, null=False, db_index=True)
    created = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(null=False)
