#!/bin/bash -e

REST_URL="http://data.agroportal.lirmm.fr"
API_KEY=""

curl -X POST -H "Content-Type: application/json" -H "Authorization: apikey token=$API_KEY" -d '{ "acronym" : "lovinra", "name": "INRA Linked Open Vocabularies", "description" : "This slice includes the ontologies in the LOVINRA group. This list of ontologies has been established by French INRA (Esther Dzalé).", "ontologies" : ["BIOREFINERY"]}' "$REST_URL/slices"

sleep 0.5

curl -X POST -H "Content-Type: application/json" -H "Authorization: apikey token=$API_KEY" -d '{ "acronym" : "agrold", "name": "The Agronomic Linked Data (AgroLD)", "description" : "AgroLD is a RDF knowledge base that consists of data integrated from a variety of plant resources and ontologies. The aim of the is to exploit the ontologies used to annotates the data stored in the AgroLD RDF knowledge base.", "ontologies" : ["SIO", "TO", "PATO", "NCBITAXON", "GFVO", "SO", "GO", "PO"]}' "$REST_URL/slices"

sleep 0.5

curl -X POST -H "Content-Type: application/json" -H "Authorization: apikey token=$API_KEY" -d '{ "acronym" : "exclu", "name": "Exclusive AgroPortal ontologies", "description" : "This slice includes all the ontologies hosted in AgroPortal that are not in the NCBO BioPortal.", "ontologies" : ["CO_320", "CO_321", "FALDO", "BIOREFINERY", "CO_325", "CO_125", "GENO", "CO_705", "CO_715", "ONTOBIOTOPE", "CO_020", "TRANSMAT", "GR-TAX", "TRIPHASE", "CO_121", "WHEATPHENOTYPE"]}' "$REST_URL/slices"

sleep 0.5

curl -X POST -H "Content-Type: application/json" -H "Authorization: apikey token=$API_KEY" -d '{ "acronym" : "wheat", "name": "RDA Wheat Data Interoperability working group", "description" : "This slice includes the ontologies in the WHEAT group. This list of ontologies has been established by the RDA WDI.", "ontologies" : ["SIO", "TO", "CO_321", "FALDO", "EFO", "VARIO", "CDAO", "PR", "XEO", "ENVO", "CL", "PATO", "NCBITAXON", "CO_121", "BT", "GFVO", "SNPO", "PCO", "SO", "GO", "EO", "PO"]}' "$REST_URL/slices"

sleep 0.5

curl -X POST -H "Content-Type: application/json" -H "Authorization: apikey token=$API_KEY" -d '{ "acronym" : "crop", "name": "Crop Ontology Curation Tool", "description" : "This slice includes the ontologies in the CROP group. This list of ontologies has been established by Bioversity International (Elizabeth Arnaud). The slice goal is to mimic the cropontology.org web application.", "ontologies" : ["CO_320", "CO_321", "CO_325", "CO_125", "CO_705", "CO_715", "CO_020", "CO_121"]}' "$REST_URL/slices"

