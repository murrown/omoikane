from django.core.management.base import BaseCommand, CommandError
from common.util.jp_nlp import get_unconjugated, is_kanji
from quiz.models import (Expression, Association, QuizList, QuizListItem)
from subprocess import call


def last_kanji(text):
    return [c for c in text if is_kanji(c)][-1]


def num_kanji(text):
    return len([c for c in text if is_kanji(c)])


def get_kanji_strings(text):
    text = "".join([c if is_kanji(c) else ' ' for c in text])
    return text.split()


def get_all_substrings(input_string):
    length = len(input_string)
    substrings = [input_string[i:j+1]
                  for i in range(length) for j in range(i, length)]
    return substrings

class Command(BaseCommand):
    help = "Generate a QuizList from a text file and audio file."

    def add_arguments(self, parser):
        parser.add_argument("quizlist_title", type=str)
        parser.add_argument("data_filename", type=str)
        parser.add_argument("audio_filename", type=str)

    def handle(self, *args, **options):
        get_unconjugated('')
        ql, _ = QuizList.objects.get_or_create(name=options["quizlist_title"])
        QuizListItem.objects.filter(quizlist=ql).delete()
        ex_lines = []
        start, finish, jp_text, en_text = None, None, None, None
        with open(options["data_filename"]) as data_file:
            for line in data_file.readlines():
                line = line.strip()
                if not line:
                    start, finish, jp_text, en_text = None, None, None, None
                    continue
                try:
                    start, finish = map(float, line.split())
                    continue
                except ValueError:
                    pass
                if start is None or finish is None:
                    continue
                if jp_text is None:
                    jp_text = line.replace("　", " ")
                    continue
                en_text = line
                ex, _ = Expression.objects.get_or_create(text=jp_text)
                if ex not in ex_lines:
                    ex_lines.append(ex)
                assoc, _ = Association.objects.get_or_create(
                    expression=ex, sense=en_text, sense_number=0)
                if finish > start >= 0:
                    ex.audio = "{0:0>8}.opus".format(ex.id)
                    ex.save()
                    cmd = ["ffmpeg", "-i", options["audio_filename"],
                           "-acodec", "libopus", "-vbr", "1", "-ac", "1",
                           "-ss", "%s" % start, "-t", "%s" % (finish-start),
                           "-map", "0:a", "-y", ex.audio]
                    call(cmd)
                start, finish, jp_text, en_text = None, None, None, None

        def get_sort_key(ex):
            return (ex_line.text.index(last_kanji(ex.text)),
                    num_kanji(ex.text),
                    ex_line.text.index(ex.text if ex.text in ex_line.text
                                       else ex.text[0]),
                    len(ex.text), -ex.priority, ex.id)

        for ex_line in ex_lines:
            kanji_strings = set([])
            for line_slice in ex_line.text.replace('　', ' ').split():
                for k in get_all_substrings(line_slice):
                    kanji_strings.add(k)

            kanji_strings = [s for s in kanji_strings if s and is_kanji(s[0])]

            new_exs = []
            for kanji_string in sorted(
                    kanji_strings, key=lambda ks: len(ks), reverse=True):
                exs = Expression.objects.filter(text__startswith=kanji_string)
                exs = [ex for ex in exs
                       if not any(is_kanji(c) and c not in kanji_string
                                  for c in ex.text)]
                my_exs = []
                for ex in exs:
                    if ex.text in ex_line.text:
                        my_exs.append(ex)
                for unconjugated in get_unconjugated(kanji_string):
                    try:
                        my_exs.append(
                            Expression.objects.get(text=unconjugated))
                    except Expression.DoesNotExist:
                        pass
                new_exs.extend(my_exs)

            exs = sorted(set(new_exs), key=get_sort_key)
            if ex_line in exs:
                exs.remove(ex_line)
            print()
            print(ex_line.pretty_summary)
            for ex in exs:
                qli = ql.add_item(ex, ignore_duplicate=True)
                print(qli.expression.pretty_summary)
            ql.add_item(ex_line, ignore_duplicate=True)
