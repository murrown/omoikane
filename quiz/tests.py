from django.test import TestCase

from quiz.models import (
    Expression, Association, UserExpression, UserGuess, QuizList, QuizListItem,
    ExpressionKeyValue, ReadingKeyValue, SenseKeyValue)
from quiz.user_models import User
import json

class TestViews(TestCase):
    def setUp(self):
        data = [("一", "いち", "one"),
                ("二", "に", "two"),
                ("三", "さん", "three"),]
        ql = QuizList.objects.create(name="test_quizlist")
        for text, reading, sense in data:
            e = Expression.objects.create(text=text)
            Association.objects.create(
                expression=e, reading=reading, sense=sense, sense_number=1)
            ql.add_item(e)
        u1 = User.objects.create(username="test_user")
        u1.set_password("test_password")
        u1.save()
        self.assertEquals(Expression.objects.count(), 3)
        self.assertEquals(Association.objects.count(), 3)
        self.assertEquals(UserExpression.objects.count(), 0)
        self.assertEquals(UserGuess.objects.count(), 0)
        self.assertEquals(User.objects.count(), 2)
        self.assertEquals(QuizList.objects.count(), 1)
        self.assertEquals(QuizListItem.objects.count(), 3)

    def test_correct_answer(self):
        user = User.objects.get(username="test_user")
        text = "一"
        self.assertTrue(self.client.login(username=user.username,
                                          password="test_password"))
        self.assertEquals(
            len(UserExpression.get_due_expressions(user=user)), 0)
        self.client.generic("POST", "/quiz/post/success",
                            "expression=%s" % text)
        self.assertEquals(UserGuess.objects.filter(
            user_expression__user=user,
            user_expression__expression__text=text, success=True).count(), 1)
        self.assertEquals(UserGuess.objects.count(), 1)
        self.assertEquals(
            len(UserExpression.get_due_expressions(user=user)), 0)

    def test_incorrect_answer(self):
        user = User.objects.get(username="test_user")
        text = "一"
        self.assertTrue(self.client.login(username=user.username,
                                          password="test_password"))
        self.assertEquals(
            len(UserExpression.get_due_expressions(user=user)), 0)
        self.client.generic("POST", "/quiz/post/failure",
                            "expression=%s" % text)
        self.assertEquals(UserGuess.objects.filter(
            user_expression__user=user,
            user_expression__expression__text=text, success=False).count(), 1)
        self.assertEquals(UserGuess.objects.count(), 1)
        self.assertEquals(
            len(UserExpression.get_due_expressions(user=user)), 1)

    def test_get_due(self):
        user = User.objects.get(username="test_user")
        ql = QuizList.objects.get()
        self.assertTrue(self.client.login(username=user.username,
                                          password="test_password"))
        self.assertEquals(
            len(UserExpression.get_due_expressions(user=user)), 0)
        response = self.client.generic("POST", "/quiz/post/due",
                                       "quizlist=%s" % ql.id)
        content = json.loads(response.content)
        self.assertEquals(content,
            {'results': [{'expression': '一',
                          'readings': ['いち', 'ichi'],
                          'associations': [{'sense': 'one',
                                            'reading': 'いち'}],
                          'audio': ''}]})
        self.assertEquals(
            len(UserExpression.get_due_expressions(user=user)), 1)

    def test_get_lists(self):
        ql = QuizList.objects.get()
        response = self.client.generic("GET", "/quiz/get/lists")
        content = json.loads(response.content)
        self.assertEquals(len(content["results"]), 1)
        self.assertEquals(content["results"][0]["name"], ql.name)
        self.assertEquals(content["results"][0]["done"], 0)
        self.assertEquals(content["results"][0]["tried"], 0)
        self.assertEquals(content["results"][0]["total"], len(ql.expressions))

        self.client.generic("POST", "/quiz/post/failure", "expression=一")
        response = self.client.generic("GET", "/quiz/get/lists")
        content = json.loads(response.content)
        self.assertEquals(content["results"][0]["done"], 0)
        self.assertEquals(content["results"][0]["tried"], 1)

        self.client.generic("POST", "/quiz/post/success", "expression=一")
        response = self.client.generic("GET", "/quiz/get/lists")
        content = json.loads(response.content)
        self.assertEquals(content["results"][0]["done"], 1)
        self.assertEquals(content["results"][0]["tried"], 1)
