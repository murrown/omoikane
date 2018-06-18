from django.db import models
from django.db.models import Q, F
from .definition_models import Expression, Association


class KeyValue(models.Model):
    entry_id = models.IntegerField(null=False, db_index=True)
    key = models.CharField(max_length=24, null=False, db_index=True)
    value = models.TextField(default="", db_index=True)

    class Meta:
        abstract = True

    def __str__(self):
        return "%s:%s" % (self.key, self.value)


class ExpressionKeyValue(KeyValue):
    expression = models.ForeignKey(Expression, null=False, db_index=True)

    class Meta:
        index_together = [("key", "value")]
        unique_together = ("key", "value", "entry_id", "expression")

    def __str__(self):
        return "%s %s" % (self.expression.text,
                          super(ExpressionKeyValue, self).__str__())


class ReadingKeyValue(KeyValue):
    reading = models.CharField(max_length=75, null=False)

    class Meta:
        index_together = [("key", "value")]
        unique_together = ("key", "value", "entry_id", "reading")

    def __str__(self):
        return "%s %s" % (self.reading,
                          super(ReadingKeyValue, self).__str__())


class SenseKeyValue(KeyValue):
    sense_number = models.IntegerField(null=False)

    class Meta:
        index_together = [("key", "value")]
        unique_together = ("key", "value", "entry_id", "sense_number")

    def __str__(self):
        return "%s.%s %s" % (self.entry_id, self.sense_number,
                             super(SenseKeyValue, self).__str__())



def calculate_priority_all():
    Association.objects.all().update(priority=0)
    point_values = {
        "news1": 13000,
        "news2": 1000,
        "ichi1": 15000,
        "ichi2": 7500,
        "spec1": 10000,
        "spec2": 5000,
        "gai1": 0,
        "gai2": 0,
        #nfxx: ???
        #nf01: 0-500
        #nf48: 23500-24000
        }
    for i in range(1, 49):
        assert 1 <= i <= 48
        point_values["nf{0:0>2}".format(i)] = 25000 - (500 * (i-1))
    roots = set([''.join(c for c in key if c not in "0123456789")
                 for key in point_values if point_values[key] > 0])

    assocs = (Association.objects.exclude(expression=None)
                                 .exclude(reading=None))
    num_total = assocs.count()
    for i, assoc in enumerate(assocs):
        if not i % 1000:
            print("%s / %s" % (i, num_total))
        ekv = (ExpressionKeyValue.objects
            .filter(key="ke_pri", expression=assoc.expression,
                    entry_id=assoc.entry_id)
            .distinct('value').values_list('value', flat=True))
        rkv = (ReadingKeyValue.objects
            .filter(key="re_pri", entry_id=assoc.entry_id,
                    reading=assoc.reading)
            .distinct('value').values_list('value', flat=True))
        kvs = set(ekv) | set(rkv)

        if kvs:
            chosen = set([])
            for root in roots:
                root_kvs = [kv for kv in kvs if kv.startswith(root)]
                if len(root_kvs) > 1:
                    chosen.add(max(root_kvs, key=lambda x: point_values[x]))
                elif len(root_kvs) == 1:
                    chosen.add(root_kvs[0])
                else:
                    continue
            assoc.priority = sum(point_values[c] for c in chosen)
            assoc.save()
