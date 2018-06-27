from collections import defaultdict

VERB_SUFFIX_FILENAME = "japanese_verb_conjugations.txt"
verb_suffix_dictionary = defaultdict(set)

with open(VERB_SUFFIX_FILENAME) as f:
    for line in f.readlines():
        line = line.strip().split()
        dictionary_form, suffixes = line[0], line[1:]
        for suffix in suffixes:
            verb_suffix_dictionary[suffix].add(dictionary_form)


def get_unconjugated(verb):
    candidates = set([])
    for suffix in verb_suffix_dictionary:
        if verb.endswith(suffix):
            for root in verb_suffix_dictionary[suffix]:
                dictionary_form = (verb[:-len(suffix)] + root)
                candidates.add(dictionary_form)
    candidates.add(verb + "る")
    return candidates


def is_kanji(c):
    return 0x4e00 <= ord(c) <= 0x9fff
