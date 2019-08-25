# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Colin Sippl.
#
# This file is part of charter-abstracts.
#
# Charter-abstracts is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Charter-abstracts is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Foobar.  If not, see <http://www.gnu.org/licenses/>.

"""
In this class, charter abstracts of Katharinenspital's regesta files are analysed using spaCy.
The default language processing pipeline of spaCy consists of a tagger, a parser and an entity recognizer.
Each pipeline component returns the processed Doc, which is then passed on to the next component.

See: https://spacy.io/usage/processing-pipelines

Afterwards, the extracted named entities and relationships are translated into CIDOC-CRM classes.

There are also other ways to extract relations between NEs:

Once named entities have been identified in a text, we then want to extract the relations that exist between them.
As indicated earlier, we will typically be looking for relations between specified types of named entity. One way of
approaching this task is to initially look for all triples of the form (X, α, Y), where X and Y are named entities
of the required types, and α is the string of words that intervenes between X and Y...

https://www.nltk.org/book/ch07.html#sec-relextract

"""
from __future__ import unicode_literals
import spacy
from spacy.attrs import intify_attrs
import sys

reload(sys)
sys.setdefaultencoding('utf8')


class NLP:

    def __init__(self):
        self.nlp = spacy.load('de_core_news_sm')


    def analyze_dep(self, doc):
        """
        Apply a heuristic to the dependencies. This heuristic is used to extract 'quadruples' and 'triples' from
        the rather uniform charter abstracts. Quadruples consist of a subject, a predicate, a direct object and an
        indirect object. Based on the extracted deps further information may be added to the direct and indirect
        objects, e.g. if a direct object can be identified as a 'E53Place' crm class.

        This heuristic approach is experimental and inevitably will be creating false positives. It heavily depends
        on the language model used by spaCy, too.

        :param doc: spaCy doc object
        :return: quadruple or triple
        """
        subject = ''
        verb = ''
        dobject = ''
        dobject2 = ''
        index = 0
        # these prepositions are used to check if a noun is a place
        loc_att = ['im', 'zu', 'gegenüber', 'in', 'neben', 'beim', 'bei', 'samt']
        # these prepositions are used to analyse and determine a 'E30Right'
        right_att = ['durch', 'auf', 'von', 'über', 'um']
        # iterate through every token
        for token in doc:
            # try to extract subject
            if token.dep_ == "sb" or token.dep_ == "oa" or token.dep_ == "da" or token.dep_ == "mnr":
                # get subject
                if token.dep_ == "sb" and index == 0:
                    subject = token.text
                    # force uniform spelling of 'St. Katharinenspital'
                    if subject == "Spital" or subject == "St.-Katharinenspital" or subject == "Katharinenspital":
                        subject = "St. Katharinenspital"
                # get verb of subject 'What does X?'
                if token.dep_ == "sb" and index == 0 and token.head.pos_ == "VERB":
                    # manually fix a lemmatization problem
                    if token.head.lemma_ == "verstiftet":
                        verb = "verstiften"
                    else:
                        verb = token.head.lemma_
                # get direct object
                print(index, token.dep_, token.head.pos_)
                if index == 1 and (token.dep_ == "da" or token.dep_ == "oa") and token.head.pos_ == "VERB":
                    dobject = token.text
                    # force uniform spelling of 'St. Katharinenspital'
                    if dobject == "Spital" or dobject == "St.-Katharinenspital" or dobject == "Katharinenspital":
                        dobject = "St. Katharinenspital"
                    # resolve reflexive pronoun
                    if dobject == "sich":
                        dobject = subject
                # get indirect object
                if index == 2 and token.dep_ == "oa":
                    dobject2 = token.text
                # check if indirect object is location or right
                if token.dep_ == 'mnr' and token.head.text == dobject2:
                    tree = [child.lemma_ for child in token.children if child.pos_ == 'NOUN' or child.pos_ == 'PROPN']
                    if tree:
                        if token.text in loc_att:
                            dobject2 = (dobject2, tree[0])
                        elif token.text in right_att:
                            dobject2 = ("E30Right", dobject2)
                index += 1
        print(subject, verb, dobject, dobject2)
        if subject != '' and verb != '' and dobject != '' and dobject2 != '':
            return self.check_subject(subject, doc), verb, dobject, dobject2
        if subject != '' and verb != '' and dobject:
            return self.check_subject(subject, doc), verb, dobject
        if subject != '' and verb != '':
            return self.check_subject(subject, doc), verb
        return ''

    def check_subject(self, subject, doc):
        """
        Merge multi-word proper nouns like 'Hainreich von Trautenberch' into a single token

        :param subject: the subject of a sentence
        :param doc: the spaCy document object
        :return: the new merged token
        """
        noun = subject
        if doc[1].pos_ == 'DET' and doc[2].pos_ == 'NOUN':
            noun = doc[0].text + ' ' + doc[1].text + ' ' + doc[2].text
        return noun

    def spacy_dependency_parse(self, charter_abstract):
        """
        Execute spaCy NLP pipeline for charter abstracts

        :param charter_abstract: the charter abstract
        :return: the spaCy doc object
        """
        # Attention during sentence segmentation. The German model of spaCy tends to recognise some elements too quickly
        # as a sentence, see:  https://github.com/explosion/spaCy/issues/1756 and
        # https://spacy.io/usage/linguistic-features#sbd

        # Lemmatisation issues
        # Merge NEs into a single token: https://github.com/explosion/spaCy/issues/2193
        # Lemmatise NEs https://github.com/explosion/spaCy/issues/1809
        # Issues with spaCy German lemmatiser (1) https://github.com/explosion/spaCy/issues/2486
        # Issues with spaCy German lemmatiser (2) https://github.com/explosion/spaCy/issues/2668

        doc = self.nlp(charter_abstract.decode('utf-8'))
        # get named entities
        entities = [(ent.start, ent.end, ent.label, ent.lemma_)
                for ent in doc.ents]

        # merge and retokenize named entities
        with doc.retokenize() as retokenizer:
            string_store = doc.vocab.strings
            for start, end, label, lemma in entities:
                retokenizer.merge(
                    doc[start: end],
                    attrs=intify_attrs({'ent_type': label, 'lemma': lemma}, string_store))

        return doc
