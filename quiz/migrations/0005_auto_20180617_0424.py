# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-06-17 04:24
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def populate_expressions(apps, schema_editor):
    Association = apps.get_model("quiz", "Association")
    Expression = apps.get_model("quiz", "Expression")

    expression_texts = sorted(
        Association.objects.exclude(expression=None).values_list("expression", flat=True).distinct())
    '''
    num_total = len(expression_texts)
    for i, et in enumerate(expression_texts):
        if not i % 100:
            print("%s / %s" % (i, num_total))
        Expression.objects.create(text=et, audio=None)
    '''
    Expression.objects.bulk_create(
        [Expression(text=et, audio=None) for et in expression_texts])


def update_expression_foreign_keys(apps, schema_editor):
    Association = apps.get_model("quiz", "Association")
    QuizListItem = apps.get_model("quiz", "QuizListItem")
    UserExpression = apps.get_model("quiz", "UserExpression")
    Expression = apps.get_model("quiz", "Expression")
    for mymodel in [Association, QuizListItem, UserExpression]:
        num_total = mymodel.objects.count()
        for i, a in enumerate(mymodel.objects.all()):
            if not i % 100:
                print("%s / %s" % (i, num_total))
            if hasattr(a, "expression_text"):
                if a.expression_text is not None:
                    a.expression = Expression.objects.get(text=a.expression_text)
                    a.save()
            else:
                if a.expression is not None:
                    a.expression = Expression.objects.get(text=a.expression)
                    a.save()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('quiz', '0004_auto_20180612_0719'),
    ]

    operations = [
        migrations.CreateModel(
            name='Expression',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(db_index=True, max_length=100, null=True, unique=True)),
                ('audio', models.CharField(max_length=32, null=True, unique=True)),
            ],
        ),
        migrations.RunPython(populate_expressions),
        migrations.RemoveField(
            model_name='userguess',
            name='user',
        ),
        migrations.AddField(
            model_name='userguess',
            name='user_expression',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, to='quiz.UserExpression'),
            preserve_default=False,
        ),
        migrations.RenameField("Association", "expression", "expression_text"),
        migrations.RenameField("QuizListItem", "expression", "expression_text"),
        migrations.RenameField("UserExpression", "expression", "expression_text"),
        migrations.AddField(
            model_name='association',
            name='expression',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='quiz.Expression'),
        ),
        migrations.AlterField(
            model_name='association',
            name='reading',
            field=models.CharField(max_length=75, null=True),
        ),
        migrations.AddField(
            model_name='quizlistitem',
            name='expression',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='quiz.Expression'),
        ),
        migrations.AddField(
            model_name='userexpression',
            name='expression',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='quiz.Expression'),
        ),
        migrations.RunPython(update_expression_foreign_keys),
        migrations.RemoveField(
            model_name='association',
            name='expression_text',
        ),
        migrations.RemoveField(
            model_name='quizlistitem',
            name='expression_text',
        ),
        migrations.RemoveField(
            model_name='userexpression',
            name='expression_text',
        ),
        migrations.AlterIndexTogether(
            name='userexpression',
            index_together=set([('user', 'expression')]),
        ),
    ]
