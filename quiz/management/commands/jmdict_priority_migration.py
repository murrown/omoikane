# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from quiz.models import (Expression, ExpressionKeyValue, ReadingKeyValue)
from django.db.utils import IntegrityError
import xml.etree.ElementTree as ET

LANG = "{http://www.w3.org/XML/1998/namespace}lang"
references = []


MIN_KANA = u"\u3040"
MAX_KANA = u"\u30ff"


def is_kana(char):
    if MIN_KANA <= char <= MAX_KANA:
        return True
    else:
        return False


class EntryProfile:
    def __init__(self):
        self.k_objs, self.r_objs = [], []
        self.pos = None

    def make_k_ele(self, k_ele):
        for child in k_ele:
            if child.text:
                child.text = child.text.strip()

            if child.tag == 'keb':
                #expression in kanji
                k_obj = child.text
                self.k_objs.append(k_obj)
            elif child.tag == 'ke_pri':
                #misc. info
                try:
                    ExpressionKeyValue.objects.get_or_create(
                        entry_id=self.entry_id,
                        expression=Expression.objects.get(text=k_obj),
                        key=child.tag, value=child.text or "")
                except:
                    print("ERROR %s %s" % (self.entry_id, k_obj))

    def make_r_ele(self, r_ele):
        if self.k_objs:
            return
        for child in r_ele:
            if child.text:
                child.text = child.text.strip()

            if child.tag == 'reb':
                #reading in kana
                r_obj = child.text
                self.r_objs.append(r_obj)
            elif child.tag == 're_pri':
                #misc. info
                try:
                    ReadingKeyValue.objects.get_or_create(
                        entry_id=self.entry_id, reading=r_obj,
                        key=child.tag, value=child.text or "")
                except:
                    print("ERROR %s %s" % (self.entry_id, r_obj))


def migrate():
    print("Parsing dictionary.")
    DICT_FILE = 'JMdict'
    root = ET.parse(DICT_FILE).getroot()

    total_entries = len(root)
    print("Dictionary parsed. %s entries found." % total_entries)
    print("Beginning migration.")
    counter = 0
    for entry in root:
        if not counter % 10000:
            print("%s / %s entries migrated." % (counter, total_entries))
        counter += 1

        e = EntryProfile()
        for child in entry:
            if child.tag == 'ent_seq':
                e.entry_id = int(child.text)
            elif child.tag == 'k_ele':
                e.make_k_ele(child)
            elif child.tag == 'r_ele':
                e.make_r_ele(child)


class Command(BaseCommand):
    help = "Migrates JMdict priority key-values to database."

    def handle(self, *args, **options):
        migrate()
