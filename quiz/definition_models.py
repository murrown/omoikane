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
    text = models.CharField(max_length=75, null=False, db_index=True)
    entry_id = models.IntegerField(db_index=True)

    class Meta:
        unique_together = ("text", "entry_id")

    def __str__(self):
        return "%s %s" % (self.entry_id, self.text)

    @staticmethod
    def get_words_with_kanji(kanjis):
        from utils import is_kanji
        query = Q()
        for k in kanjis:
            query |= Q(text__contains=k)
        exps = Expression.objects.filter(query)
        result = []
        for e in exps:
            for k in e.text:
                if is_kanji(k) and k not in kanjis:
                    break
            else:
                result.append(e)
        return result


class Reading(models.Model):
    text = models.CharField(max_length=75, null=False, db_index=True)
    entry_id = models.IntegerField(db_index=True)

    class Meta:
        unique_together = ("text", "entry_id")

    def __str__(self):
        return "%s %s" % (self.entry_id, self.text)


class Sense(models.Model):
    text = models.TextField(null=False)
    pos = models.CharField(max_length=100, default="")
    entry_id = models.IntegerField(db_index=True)
    sense_id = models.IntegerField(db_index=True)

    class Meta:
        unique_together = [("text", "entry_id"),
                           ("sense_id", "entry_id")]

    def __str__(self):
        return "%s.%s %s" % (self.entry_id, self.sense_id, self.text)


class Association(models.Model):
    expression = models.ForeignKey(Expression, null=True)
    reading = models.ForeignKey(Reading, null=False)
    sense = models.ForeignKey(Sense, null=False)
    entry_id = models.IntegerField(db_index=True)
    priorities = models.IntegerField(db_index=True, default=0)

    class Meta:
        unique_together = ("expression", "reading", "sense")
        index_together = [("expression", "reading")]

    def __str__(self):
        if self.expression:
            return "%s,%s,%s" % (self.expression.text,
                                 self.reading.text, self.sense.sense_id)
        else:
            return "%s,%s" % (self.reading.text, self.sense.sense_id)
