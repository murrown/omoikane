# -*- coding: utf-8 -*-
from django.db import models
from django.db.models import Q


RISQUE_VALUES = [
    "rude or X-rated term (not displayed in educational software)",
    "colloquialism",
    "derogatory",
    "vulgar expression or word",
    "often derog.",
    ]


class Expression(models.Model):
    text = models.CharField(max_length=100, null=True,
                            db_index=True, unique=True)
    audio = models.CharField(max_length=32, null=True, unique=True)


class Association(models.Model):
    entry_id = models.IntegerField(null=False, db_index=True)
    expression = models.ForeignKey(Expression, null=True, db_index=True)
    reading = models.CharField(max_length=75, null=True)
    sense = models.TextField(null=False)
    sense_number = models.IntegerField()
    pos = models.CharField(max_length=100, default="")

    class Meta:
        unique_together = ("expression", "reading", "sense")

    def __str__(self):
        if self.expression:
            return "%s,%s,%s" % (self.expression.text, self.reading, self.sense)
        else:
            return "%s,%s" % (self.reading, self.sense)
