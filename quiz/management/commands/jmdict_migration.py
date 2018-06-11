# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from quiz.models import (Expression, ExpressionKeyValue, Reading,
                         ReadingKeyValue, Sense, SenseKeyValue,
                         SenseCrossRef, SenseAntonym, Association)
from django.db.utils import IntegrityError
import xml.etree.ElementTree as ET

LANG = "{http://www.w3.org/XML/1998/namespace}lang"
references = []

NORMAL = True
REFERENCES_ONLY = not NORMAL


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
        self.assocs = []
        self.r_objs_ks = {}
        self.pos = None

    def __repr__(self):
        s = ""
        for a in self.assocs:
            s = "%s\n%s" % (s, a)
        return s.strip()

    def make_k_ele(self, k_ele):
        for child in k_ele:
            if child.text:
                child.text = child.text.strip()

            if child.tag == 'keb':
                #expression in kanji
                k_obj = Expression(text=child.text, entry_id=self.entry_id)
                k_obj.save()
                self.k_objs.append(k_obj)
            elif child.tag in ['ke_inf', 'ke_pri']:
                #misc. info
                ekv = ExpressionKeyValue(expression=k_obj,
                                         key=child.tag,
                                         value=child.text or "")
                ekv.save()

    def make_r_ele(self, r_ele):
        if not self.k_objs:
            return
        for child in r_ele:
            if child.text:
                child.text = child.text.strip()

            if child.tag == 'reb':
                #reading in kana
                r_obj = Reading(text=child.text, entry_id=self.entry_id)
                r_obj.save()
                self.r_objs.append(r_obj)
                self.r_objs_ks[r_obj] = []
            elif child.tag == 're_restr':
                #restriction to keb
                valid_ks = [k for k in self.k_objs if k.text == child.text]
                assert len(valid_ks) == 1
                self.r_objs_ks[r_obj].append(valid_ks[0])
            elif child.tag in ['re_inf', 're_pri', 're_nokanji']:
                #misc. info
                rkv = ReadingKeyValue(reading=r_obj, key=child.tag,
                                      value=child.text or "")
                try:
                    rkv.save()
                except Exception as e:
                    print(e)
                    import pdb; pdb.set_trace()

    def make_sense(self, sense):
        if not self.k_objs:
            return
        s_obj = Sense(text="...", entry_id=self.entry_id,
                      sense_id=len(self.s_objs))
        s_obj.save()
        self.s_objs.append(s_obj)

        glosses, stagks, stagrs = [], [], []
        for child in sense:
            if child.text:
                child.text = child.text.strip()

            if child.tag == 'stagk':
                #restriction to expression
                valid_ks = [k for k in self.k_objs if k.text == child.text]
                assert len(valid_ks) == 1
                stagks.append(valid_ks[0])
            elif child.tag == 'stagr':
                #restriction to reading
                valid_rs = [r for r in self.r_objs if r.text == child.text]
                assert len(valid_rs) == 1
                stagrs.append(valid_rs[0])
            elif child.tag == 'pos':
                #applies to future senses unless otherwise specified
                self.pos = child.text
            elif child.tag == 'gloss':
                #will always be in english unless xml:lang present
                if (LANG in dict(child.items()) and
                        'eng' not in dict(child.items()).values()):
                    continue
                glosses.append(child.text)
            elif child.tag == 'lsource':
                #source language
                _, language = child.items()[0]
                value = "%s: %s" % (language, child.text)
                skv = SenseKeyValue(sense=s_obj, key=child.tag,
                                    value=value.strip())
                skv.save()
            elif child.tag in ['xref', 'ant']:
                #reference another profile
                references.append((s_obj, child.tag, child.text))
            elif child.tag in ['pos', 'field', 'misc', 'dial', 's_inf']:
                #misc. info
                skv = SenseKeyValue(sense=s_obj, key=child.tag,
                                    value=child.text or "")
                skv.save()

        try:
            glosses_text = "; ".join(glosses)
            new_text = glosses_text
            counter = 1
            while True:
                try:
                    Sense.objects.get(text=new_text,
                                      entry_id=s_obj.entry_id)
                    counter += 1
                    new_text = glosses_text + (" (%s)" % counter)
                except Sense.DoesNotExist:
                    break

            s_obj.text = new_text
            s_obj.pos = self.pos
            s_obj.save()

            stagrs = stagrs or self.r_objs
            stagks = stagks or self.k_objs or [None]
            for r in stagrs:
                if self.r_objs_ks[r]:
                    valid_ks = [k for k in stagks if k in self.r_objs_ks[r]]
                else:
                    valid_ks = stagks
                for k in stagks:
                    a = Association(expression=k, reading=r,
                                    sense=s_obj, entry_id=self.entry_id)
                    a.save()
                    self.assocs.append(a)
        except Exception as e:
            print(e)
            print(s_obj.entry_id)
            import pdb; pdb.set_trace()

            self.s_objs.remove(s_obj)
            s_obj.delete()


def migrate():
    print("Parsing dictionary.")
    DICT_FILE = 'JMdict'
    root = ET.parse(DICT_FILE).getroot()

    total_entries = len(root)
    print("Dictionary parsed. %s entries found." % total_entries)
    print("Beginning migration.")
    counter = 0
    for entry in root:
        counter += 1
        if not counter % 10000:
            print("%s entries migrated." % counter)

        if NORMAL:
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
            print("%s / %s" % (counter, total_entries))
            print(str(e)+"\n")

        elif REFERENCES_ONLY:
            ent_seq = None
            sense_id = 0
            kebs = []
            rebs = []
            for child in entry:
                if child.tag == 'ent_seq':
                    ent_seq = int(child.text)
                elif child.tag == 'k_ele':
                    for k_chi in child:
                        if k_chi.tag == 'keb':
                            kebs.append(k_chi.text)
                elif child.tag == 'r_ele':
                    for r_chi in child:
                        if r_chi.tag == 'reb':
                            rebs.append(r_chi.text)
                elif child.tag == 'sense':
                    sense_id += 1
                    for s_chi in child:
                        if s_chi.tag in ['xref', 'ant']:
                            s_obj = Sense.objects.get(entry_id=ent_seq,
                                                      sense_id=sense_id)
                            if kebs:
                                references.append((s_obj, s_chi.tag,
                                                   s_chi.text, kebs))
                            elif rebs:
                                references.append((s_obj, s_chi.tag,
                                                   s_chi.text, rebs))

    print("%s references found" % len(references))
    counter = 0
    for sense, relation, item, texts in references:
        counter += 1
        if not counter % 1000:
            print("%s entries migrated." % counter)

        if all(map(is_kana, item)):
            k_item, r_item, s_item = "", item, -1
        else:
            items = item.split("・".decode("utf8"))
            if items[-1].isdigit():
                s_item = int(items[-1])
                items = items[:-1]
            else:
                s_item = -1

            if len(items) == 2:
                k_item, r_item = tuple(items)
            elif all(map(is_kana, items[0])):
                k_item, r_item = "", items[0]
            else:
                k_item, r_item = items[0], ""

        if not (k_item or r_item):
            print("wtf")
            continue

        assocs = Association.objects.all()
        if s_item and s_item > 0:
            assocs = assocs.filter(sense__sense_id=s_item)
        if k_item:
            assocs = assocs.filter(expression__text=k_item)
        if r_item:
            assocs = assocs.filter(reading__text=r_item)

        assocs = assocs.order_by('-priorities')
        if not assocs.exists():
            print("ERROR: No appropriate entries found.")
            print("Sense: %s %s" % (sense.entry_id, sense.sense_id))
            print("Reference: %s\n" % item)
            assoc = None
        elif assocs.count() == 1:
            assoc = assocs[0]
        else:
            assoc = None

        if relation == "xref":
            Klass = SenseCrossRef
        elif relation == "ant":
            Klass = SenseAntonym

        for text in texts:
            k = Klass(base_text=text, base_sense=sense, sense_id=s_item,
                      exp_text=k_item, read_text=r_item, association=assoc)
            try:
                k.save()
            except IntegrityError as e:
                print(e)
                print("Duplicate: %s" % k)

class Command(BaseCommand):
    help = "Migrates JMdict to database."

    def handle(self, *args, **options):
        migrate()
