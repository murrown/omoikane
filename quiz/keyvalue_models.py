from django.db import models
from .definition_models import Expression, Reading, Sense


class KeyValue(models.Model):
    key = models.CharField(max_length=24, null=False, db_index=True)
    value = models.TextField(default="")

    class Meta:
        abstract = True

    def __str__(self):
        return "%s:%s" % (self.key, self.value)


class ExpressionKeyValue(KeyValue):
    expression = models.ForeignKey(Expression, null=False)

    class Meta:
        index_together = [("key", "expression")]

    def __str__(self):
        return "%s %s" % (self.expression.text,
                          super(ExpressionKeyValue, self).__str__())


class ReadingKeyValue(KeyValue):
    reading = models.ForeignKey(Reading, null=False)

    class Meta:
        index_together = [("key", "reading")]

    def __str__(self):
        return "%s %s" % (self.reading.text,
                          super(ReadingKeyValue, self).__str__())


class SenseKeyValue(KeyValue):
    sense = models.ForeignKey(Sense, null=False)

    class Meta:
        index_together = [("key", "sense")]

    def __str__(self):
        return "%s.%s %s" % (self.sense.entry_id, self.sense.sense_id,
                             super(SenseKeyValue, self).__str__())
