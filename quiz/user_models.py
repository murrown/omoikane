from django.db import models
from django.contrib.auth.models import User

from datetime import datetime
from pytz import utc
from .definition_models import Expression


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


class UserGuess(models.Model):
    user = models.ForeignKey(User, null=False, db_index=True)
    created = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(null=False)
