from django.db import models
from .definition_models import Expression


class QuizList(models.Model):
    name = models.CharField(max_length=32, primary_key=True)

    def add_item(self, expression):
        num_items = QuizListItem.objects.filter(quizlist=self).count() + 1
        qli = QuizListItem(quizlist=self, expression=expression,
                           list_order=num_items)
        qli.save()
        return qli


class QuizListItem(models.Model):
    quizlist = models.ForeignKey(QuizList, null=False, db_index=True)
    expression = models.ForeignKey(Expression, null=False)
    list_order = models.IntegerField(null=False)

    class Meta:
        unique_together = [("quizlist", "expression"),
                           ("quizlist", "list_order")]
