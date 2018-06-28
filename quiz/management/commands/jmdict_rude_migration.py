# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from quiz.models import (Expression, Association, SenseKeyValue)
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
        self.k_objs, self.r_objs, self.s_objs = [], [], []
        self.pos = None

    def make_k_ele(self, k_ele):
        for child in k_ele:
            if child.text:
                child.text = child.text.strip()

            if child.tag == 'keb':
                #expression in kanji
                k_obj = child.text
                self.k_objs.append(k_obj)

    def make_r_ele(self, r_ele):
        for child in r_ele:
            if child.text:
                child.text = child.text.strip()

            if child.tag == 'reb':
                #reading in kana
                r_obj = child.text
                self.r_objs.append(r_obj)

    def make_sense(self, sense):
        self.s_objs.append(sense)

        for child in sense:
            if child.text:
                child.text = child.text.strip()

            if child.tag in ['field', 'misc', 'dial', 's_inf']:
                #misc. info
                skv, _ = SenseKeyValue.objects.get_or_create(
                    entry_id=self.entry_id, sense_number=len(self.s_objs),
                    key=child.tag, value=child.text or "")

def migrate():
    print("Parsing dictionary.")
    DICT_FILE = 'JMdict'
    root = ET.parse(DICT_FILE).getroot()

    total_entries = len(root)
    print("Dictionary parsed. %s entries found." % total_entries)
    print("Beginning migration.")
    counter = 0
    for entry in root:
        if not counter % 1000:
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
            elif child.tag == 'sense':
                e.make_sense(child)


class Command(BaseCommand):
    help = "Migrates JMdict priority key-values to database."

    def handle(self, *args, **options):
        migrate()
