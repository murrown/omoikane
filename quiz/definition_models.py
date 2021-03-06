# -*- coding: utf-8 -*-
from django.db import models
from django.db.models import Q, CASCADE
from django.apps import apps

from more_itertools import unique_everseen
from collections import defaultdict

RISQUE_VALUES = [
    "rude or X-rated term (not displayed in educational software)",
    "colloquialism",
    "derogatory",
    "vulgar expression or word",
    ]


class Expression(models.Model):
    text = models.CharField(max_length=100, null=False,
                            db_index=True, unique=True)
    audio = models.CharField(max_length=32, null=True, unique=True)

    def __str__(self):
        return "%s %s" % (self.id, self.text)

    @property
    def priority(self):
        return max([a.priority for a in
                    Association.objects.filter(expression=self)])

    def get_summary_data(self):
        TARGET_NUMBER = 4

        assocs = list(Association.objects
                      .filter(expression=self, priority__gte=0)
                      .order_by("-priority", "entry_id", "sense_number", "id"))
        all_readings = [a.reading for a in assocs if a.reading is not None]
        all_readings = sorted(set(all_readings),
                              key=lambda ar: all_readings.index(ar))

        assocs = list(unique_everseen(
            assocs, key=lambda a: (a.entry_id, a.sense_number)))

        temp = [a for a in assocs if a.priority > 0]
        if len(temp) >= TARGET_NUMBER:
            assocs = temp

        prioritized_unique_entries = []
        entry_group_dict = defaultdict(list)

        for a in assocs:
            if a.entry_id not in prioritized_unique_entries:
                prioritized_unique_entries.append(a.entry_id)
            entry_group_dict[a.entry_id].append(a)

        diverse_selection = []
        while len(diverse_selection) < min(len(assocs), TARGET_NUMBER):
            if not prioritized_unique_entries:
                break
            pue = prioritized_unique_entries.pop(0)
            try:
                diverse_selection.append(
                    entry_group_dict[pue].pop(0))
            except IndexError:
                continue
            assert pue not in prioritized_unique_entries
            prioritized_unique_entries.append(pue)

        diverse_selection = sorted(diverse_selection,
            key=lambda a: (-a.priority, a.entry_id, a.sense_number, a.id))

        return diverse_selection, all_readings

    @property
    def pretty_summary(self):
        assocs, readings = self.get_summary_data()
        s = "-- %s\n" % self.text
        s += "\n".join([
            "%s: %s" % (a.reading, a.sense) if a.reading else a.sense
            for a in assocs])
        return s


class Association(models.Model):
    entry_id = models.IntegerField(null=True, db_index=True)
    expression = models.ForeignKey(Expression, null=True, db_index=True,
                                   on_delete=CASCADE)
    reading = models.CharField(max_length=75, null=True)
    sense = models.TextField(null=False)
    sense_number = models.IntegerField()
    pos = models.CharField(max_length=100, null=True)
    priority = models.IntegerField(default=0, db_index=True)

    class Meta:
        unique_together = ("expression", "reading", "sense")

    def __str__(self):
        if self.expression is not None:
            return "%s,%s,%s" % (
                self.expression.text, self.reading, self.sense)
        else:
            return "%s,%s" % (self.reading, self.sense)

    @property
    def is_potentially_rude(self):
        SenseKeyValue = apps.get_model("quiz", "SenseKeyValue")
        skvs = SenseKeyValue.objects.filter(
            entry_id=self.entry_id, sense_number=self.sense_number, key="misc")

        for skv in skvs:
            if skv.value in RISQUE_VALUES:
                return True
        return False
