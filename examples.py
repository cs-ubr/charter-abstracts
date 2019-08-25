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
# along with Spital-charters.  If not, see <http://www.gnu.org/licenses/>.

""" 
This file contains examples how charter regesta can be linked together in neo4j
graph database using CIDOC-CRM ontology and NLP.

 - neo4j https://neo4j.com/download-center/#community
 - cidco-crm http://www.cidoc-crm.org/
 - neomodel https://neomodel.readthedocs.io/en/latest/
 - cidoc-crm-neo4j, a meta-implementation of the CIDOC Conceptual Reference Model in Neo4j,
   using neomodel https://github.com/diging/cidoc-crm-neo4j

"""

from __future__ import unicode_literals
from crm import models
from neomodel import (config, StringProperty)
import sys
import json

reload(sys)
sys.setdefaultencoding('utf8')

# load configs
with open('config.json') as config_file:
    config_file = json.load(config_file)

config.DATABASE_URL = "bolt://" + config_file['neo4j']['user'] + ":" + config_file['neo4j']['passwd'] + "@" + \
                      config_file['neo4j']['host'] + ":7687"

# define node fields
node_fields = {

    # Node attributes
    # ===============
    #: Name of the node 
    'name': lambda: StringProperty(index=True),
    #: Archive id of object (pid)
    'arch_id': StringProperty,
    #: Monasterium id of object (pid)
    'mom_id': StringProperty,
    #: Id of a related file (e.g. document, image...)
    'file_id': StringProperty,

}

# Load crm model from crm model file
models.build_models(config_file['cidoc-crm']['schema-file'], fields=node_fields)


def do_nlp(charter_abstract, charter, charter_id):
    """
    Analyse charter abstract and create nodes and relations in neo4j

    :param charter_abstract: a short sentence or text summarising the legal content of a charter
    :param charter: the charter node that needs to be connected to its entities
    :param charter_id: the charter id used by the archive
    :return:
    """

    # execute spaCy nlp pipeline
    doc = nlp.spacy_dependency_parse(charter_abstract)
    # get triples or quadruples from deps
    dep_data = nlp.analyze_dep(doc)
    # create activity node (the verb of a sentence is seen as the 'legal activity' described in the charter)
    activity = create_crm_entity_with_name("E7Activity", dep_data[1])
    # create main actor node
    actor = create_crm_entity_with_name("E21Person", dep_data[0])
    # connect main actor node to charter node as 'participant'
    charter.P11_had_participant.connect(actor)
    # connect main actor node to activity node as 'operator'
    activity.P14_carried_out_by.connect(actor)
    # connect main actor node to activity node as 'participant'
    activity.P11_had_participant.connect(actor)
    # connect charter node to activity node
    charter.P9_consists_of.connect(activity)

    # if a quadruple was extracted from charter abstract
    # quadruple consists of following components:
    # subject, verb, dobject, dobject2
    if len(dep_data) == 4:

        # create second actor node
        actor2 = create_crm_entity_with_name("E21Person", dep_data[2])

        # connect second actor node to charter node as 'participant'
        if not charter.P11_had_participant.is_connected(actor2):
            charter.P11_had_participant.connect(actor2)

        # connect second actor node to activity node as 'participant'
        if not activity.P11_had_participant.is_connected(actor2):
            activity.P11_had_participant.connect(actor2)

        # if dobject already has a crm class
        if not isinstance(dep_data[3], basestring):

            # if dobject is 'E30Right' like 'Ablass', 'Recht', 'Streit' etc.
            if dep_data[3][0] == "E30Right":
                # create right node
                right = create_crm_entity_with_name("E30Right", dep_data[3][1])
                # connect main actor node to right node as 'right owner'
                if not actor.P75_possesses.is_connected(right):
                    actor.P75_possesses.connect(right)
                # connect second actor node to right node as 'right owner'
                if not actor2.P75_possesses.is_connected(right):
                    actor2.P75_possesses.connect(right)
                # connect right node to activity node as 'legal content'
                right.P129_is_about.connect(activity)
                # connect right node to charter node as 'legal content'
                right.P129_is_about.connect(charter)
            # if dobject is 'E53Place' like 'Regensburg', 'Gut', 'Wiese', 'Grund' etc. with further details like
            # "...[Grund] in(!) der Stadt [Regensburg]"
            else:
                # create primary place node
                place = create_crm_entity_with_name("E53Place", dep_data[3][0])
                # create secondary place node
                place2 = create_crm_entity_with_name("E53Place", dep_data[3][1])
                # connect secondary place node to primary place node like ('Grund')-[:89_falls_within]-('Regensburg')
                # and connect secondary place node to charter - this way a charter gets relationships to entities
                # like 'Gut', 'Grund', 'Wiese' etc.
                if not place2.P89_falls_within.is_connected(place):
                    place2.P89_falls_within.connect(place)
                    charter.P161_has_spatial_projection.connect(place2)
                # connect primary place node to activity node and to charter node
                if not activity.P161_has_spatial_projection.is_connected(place):
                    activity.P161_has_spatial_projection.connect(place)
                    charter.P161_has_spatial_projection.connect(place)

        # if a triple was extracted from charter abstract
        # triple consists of following components:
        # subject, verb, dobject
        else:
            # if dobject is 'E30Right' like 'Ablass', 'Recht', 'Streit' etc.
            if dep_data[3][0] == "E30Right":
                # create right node
                right = create_crm_entity_with_name("E30Right", dep_data[3])
                # connect main actor node to right node as 'right owner'
                if not actor.P75_possesses.is_connected(right):
                    actor.P75_possesses.connect(right)
                # connect second actor node to right node as 'right owner'
                if not actor2.P75_possesses.is_connected(right):
                    actor2.P75_possesses.connect(right)
                # connect right node to activity node as 'legal content'
                right.P129_is_about.connect(activity)
                # connect right node to charter node as 'legal content'
                right.P129_is_about.connect(charter)
            # if dobject is 'E53Place' like 'Regensburg', 'Gut', 'Wiese', 'Grund'
            else:
                # create place node
                place = create_crm_entity_with_name("E53Place", dep_data[3])
                # connect place node to charter and activity
                if not activity.P161_has_spatial_projection.is_connected(place):
                    activity.P161_has_spatial_projection.connect(place)
                    charter.P161_has_spatial_projection.connect(place)


def create_crm_entity_with_name(entity_type, name):
    """
    Create and return node in neo4j with crm label (if it wasn't already created)

    :param entity_type: the crm class
    :param name: the node name
    :return:
    """

    model = getattr(models, entity_type)
    entity = model.nodes.get_or_none(name=name)
    if entity is None:
        entity = model(name=name)
        entity.save()
    return entity


def example_1():
    """
    Generate example no. 1.

    A regesta graph is being created in neo4j. The entities are already identified and are
    to be created in the database and afterwards linked together.

    Charter nodes may have additional attributes like 'file_id' (name of the regesta file) or 'mom_id' (Monasterium id)
    """

    ############ create nodes #############
    # create charter node
    charter = models.E5Event(name='charter i', arch_id='SpAR Urk. 35', mom_id='12580210',
                             file_id='urk0035.txt')
    charter.save()

    # create second charter node
    charter2 = models.E5Event(name='charter ii', arch_id='SpAR Urk. 86', mom_id='12590716',
                              file_id='urk0086.txt')
    charter2.save()

    # create type node
    charter_type = models.E55Type(name='charter type')
    charter_type.save()

    # create actor 1 node
    person = models.E21Person(name='Otto Prager')
    person.save()

    # create actor 2 node
    group = models.E74Group(name='merchant class')
    group.save()

    # create actor 3 node
    person2 = models.E21Person(name='Ortlieb in Foro')
    person2.save()

    # create actor 4 node
    person3 = models.E21Person(name='Albert de Porta')
    person3.save()

    ############ create relations between nodes ###########
    charter.P2_has_type.connect(charter_type)
    charter2.P2_has_type.connect(charter_type)
    group.P107_has_current_or_former_member.connect(person)
    group.P107_has_current_or_former_member.connect(person2)
    charter.P11_had_participant.connect(group)
    charter.P11_had_participant.connect(person)
    charter.P11_had_participant.connect(person2)
    charter2.P11_had_participant.connect(person2)
    charter2.P11_had_participant.connect(person3)


def example_2(charter_abstract, charter_id):
    """
    Generate example no. 2.

    Several regesta graphs are being created in neo4j.
    1. The entities are extracted from the charter abstracts.
    2. created in the database and afterwards linked together.

    :param charter_abstract: a short sentence or text summarising the legal content of a charter
    :param charter_id: the charter id used by the archive
    :return:
    """

    # create charter node
    charter = models.E5Event(name=charter_id)
    charter.save()

    # analyse charter abstract and connect identified entity nodes to charter node
    do_nlp(charter_abstract, charter, charter_id)


if __name__ == "__main__":
    # delete db with cypher query
    from nlp import NLP
    from neo4jrestclient.client import GraphDatabase

    db = GraphDatabase("http://" + config_file['neo4j']['host'] + ":7474", username=config_file['neo4j']['user'],
                       password=config_file['neo4j']['passwd'])
    result = db.query("MATCH (n) OPTIONAL MATCH (n)-[r]-() DELETE n,r")

    # example abstracts (in German)
    charter_abstracts = [
        ("Ulrich von Abbach verkauft dem Spital sein Gut in Teingen um 15 Pfennig.", "SpAR Urk. 2101"),
        (
            "Hainreich von Trautenberch, Richter zu Storenstain (Störenstein), verschafft dem St. Katharinenspital "
            "zwei Höfe zu Pfaffenriut (Pfaffenreut).",
            "SpAR Urk. 1483"),
        (
            "Rudger der Mulnar von Chesching (Kösching) vermacht dem St. Katharinenspital zwei Äcker zu Chesching"
            " (Kösching).",
            "SpAR Urk. 799"),
        (
            "Dompropst Heinrich, der Domdekan, Pfarrer Ulrich und der Küster Otto vom Dom, die Spitalräte"
            " (gubernatores), Otto Pragaer, Ortlib in Foro, Gerwinus und Herwicus Pollex, und der Spitalmeister"
            " Bruder R. mit dem Spitalkonvent bestätigen die Testamentsverfügungen der Witwe des Ritters Konrad"
            " von Paulstorf, Livkardis.",
            "SpAR Urk. 35"),
        (
            "Bruno von Aichkirchen verkauft dem St. Katharinenspital für 3 Pfund und 60 Pfennige einen Grund in"
            " der Stadt Regensburg.",
            "SpAR Urk. 86")
    ]

    # setup nlp pipeline
    nlp = NLP()

    # execute examples and create neo4j db
    example_1()
    for charter_abstract, charter_id in charter_abstracts:
        example_2(charter_abstract, charter_id)
