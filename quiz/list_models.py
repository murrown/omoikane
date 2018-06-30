from django.db import models
from .definition_models import Expression


class QuizList(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def add_item(self, expression, ignore_duplicate=False):
        if ignore_duplicate:
            try:
                qli = QuizListItem.objects.get(quizlist=self,
                                               expression=expression)
                return qli
            except QuizListItem.DoesNotExist:
                pass
        num_items = QuizListItem.objects.filter(quizlist=self).count() + 1
        qli = QuizListItem.objects.create(
            quizlist=self, expression=expression, list_order=num_items)
        return qli

    @property
    def expressions(self):
        return QuizListItem.objects.filter(quizlist=self).order_by(
            "list_order").values_list("expression__text", flat=True)


class QuizListItem(models.Model):
    quizlist = models.ForeignKey(QuizList, null=False, db_index=True,
                                 on_delete=models.CASCADE)
    expression = models.ForeignKey(Expression, null=False,
                                   on_delete=models.CASCADE)
    list_order = models.IntegerField(null=False)

    class Meta:
        unique_together = [("quizlist", "expression"),
                           ("quizlist", "list_order")]
