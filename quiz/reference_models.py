from django.db import models
from .definition_models import Sense, Association


class Reference(models.Model):
    exp_text = models.TextField(db_index=True)
    read_text = models.TextField(db_index=True)
    sense_id = models.IntegerField(null=True)
    association = models.ForeignKey(Association, null=True)
    base_text = models.TextField(db_index=True)

    class Meta:
        abstract = True

    def __str__(self):
        if self.base_text:
            return "%s: %s %s %s" % (self.base_text, self.exp_text,
                                     self.read_text, self.sense_id)
        else:
            return "%s %s %s" % (self.exp_text,
                                 self.read_text, self.sense_id)


class SenseCrossRef(Reference):
    base_sense = models.ForeignKey(Sense, null=False, related_name="x_bs")

    class Meta:
        unique_together = [("exp_text", "read_text", "sense_id",
                            "base_sense", "base_text"),
                           ("association", "base_sense", "base_text")]


class SenseAntonym(Reference):
    base_sense = models.ForeignKey(Sense, null=False, related_name="a_bs")

    class Meta:
        unique_together = [("exp_text", "read_text", "sense_id",
                            "base_sense", "base_text"),
                           ("association", "base_sense", "base_text")]
