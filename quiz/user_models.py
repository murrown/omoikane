from django.db import models
from django.contrib.auth.models import User

from datetime import datetime, timedelta
from pytz import utc
import romkan
from .definition_models import Association, Expression


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

    def fail(self):
        self.score = self.score * self.user.profile.score_cut
        self.interval = DEFAULT_INTERVAL
        self.due = utcnow()

    def verify_reading(self, guess, readings=None):
        guess = romkan.to_roma(romkan.to_kana(guess.replace(' ', '')))
        if not readings:
            readings = set(Association.objects
                           .filter(expression=self.expression)
                           .values_list('reading', flat=True))
        readings = map(romkan.to_roma, readings)
        return guess in readings

    def guess_reading(self, guess, readings=None):
        success = self.verify_reading(guess, readings=readings)
        UserGuess.objects.create(user_expression=self, success=success)
        self.succeed() if success else self.fail()
        self.save()
        return success


class UserGuess(models.Model):
    user_expression = models.ForeignKey(
        UserExpression, null=False, db_index=True)
    created = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(null=False)
