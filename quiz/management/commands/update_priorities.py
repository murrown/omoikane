# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from quiz.keyvalue_models import calculate_priority_all
from django.db.utils import IntegrityError


class Command(BaseCommand):
    help = "Update the priorities of Association objects."

    def handle(self, *args, **options):
        calculate_priority_all()
