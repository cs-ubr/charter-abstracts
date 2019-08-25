# charter-abstracts
## general description
This project contains some examples how charter regesta can be linked together in [neo4j graph database](https://neo4j.com/download-center/#community) using [CIDOC-CRM ontology 6.2.1](http://www.cidoc-crm.org/sites/default/files/cidoc_crm_v6.2.1-2018April.rdfs). Part of the example charters are refering to 
the St. Katharinenspital in Regensburg, Germany, and can be retrieved from [Monasterium](https://www.monasterium.net/mom/DE-AKR/Urkunden/fond).

The CRM model is imposed with [cidoc-crm-neo4j](https://github.com/diging/cidoc-crm-neo4j), a meta-implementation of the CRM model in Neo4j, using [neomodel](https://neomodel.readthedocs.io/en/latest/). 
The entities (nodes) and their relationships (edges) are extracted with natural language processing using [spaCy](https://spacy.io/) and its `de_core_news_sm` language model.

## extracting data with nlp 

The core concept of this script is extracting entities and their mutual relations from charter abstracts. 

There are different ways to achieve this. The simplest option is a heuristic approach as described [here](https://www.nltk.org/book/ch07.html#sec-relextract).

> Once named entities have been identified in a text, we then want to extract the relations that exist between them.
As indicated earlier, we will typically be looking for relations between specified types of named entity. One way of
approaching this task is to initially look for all triples of the form (X, α, Y), where X and Y are named entities
of the required types, and α is the string of words that intervenes between X and Y.


By using spaCy's built in dependency parser the grammatical structure of a sentence is being analysed. The structure defines the relationships between “head” words and words which modify those heads ([read more](https://nlp.stanford.edu/software/nndep.html)). Thus, relationships between entities can be extracted based on grammar.

Using the `displacy` visualisation module is the best way to understand how spaCy’s dependency parser works:

```
import spacy
from spacy import displacy

# initialise German model
nlp = spacy.load('de_core_news_sm')
abstract = 'Ulrich v. Abbach verkauft dem Spital sein Gut in Teinigen um 15 Pfennig'

# do nlp
doc = nlp(abstract)

# create dep visualisation
displacy.serve(doc, style='dep')
```

Once the grammatical structure has been analysed, it can be used to extract "triples" or "quadruples" like this:

|subject|predicate|direct object|indirect object|
|:---:|:---:|:---:|:---:|
|Ulrich von Abbach|verkaufen|Spital|Gut|

These syntactic entities can be translated into CRM entities:

|E21Person|E7Activity|E39Actor|E53Place|
|:---:|:---:|:---:|:---:|
|Ulrich von Abbach|verkaufen|Spital|Gut|


These entities can now be linked to a charter and the identified dependencies also help you describing the relationships between the entities. 

## system requirements / configuration
In order to execute the script successfully a running neo4j server is required. The credentials and URLs need to be set in `config.json`. Also make sure that all modules are being installed properly. 

If you want to analyse German language data with spaCy, you need to download the German language model, too:

`$ python -m spacy download de_core_news_sm`  

## running the script

Create a new virtual environment and run the following commands:

`$ pipenv install`

`$ python examples.py`

If the script is being executed successfully, you should be able to see the data in neo4j. Thanks to the crm4j module the CIDOC-CRM class hierarchy is being implemented and can be used for semantic queries.


## cypher queries

### show all nodes
`MATCH (n) RETURN n`

### get 5Events that are connected via a common friend (e.g. E39Actor)
`MATCH p=(n:E5Event)-[]-(:E39Actor)-[]-(:E5Event) RETURN p`

### show db schema
`call db.schema()`

### show labels
`MATCH (n) RETURN DISTINCT count(labels(n)), labels(n)`

## license
This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see http://www.gnu.org/licenses/.

[Monasterium]: https://www.monasterium.net/mom/DE-AKR/Urkunden/fond

[Test]: https://www.monasterium.net/mom/DE-AKR/Urkunden/fond
