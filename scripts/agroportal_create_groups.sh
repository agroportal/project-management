#!/bin/sh

REST_URL="http://vm-bioportal:8080"
#REST_URL="http://data.stageportal.lirmm.fr"
#REST_URL="http://data.agroportal.lirmm.fr"
API_KEY=""


# Create groups
curl -X PUT -H "Content-Type: application/json" -H "Authorization: apikey token=$API_KEY" -d '{ "acronym": "WHEAT", "name": "Wheat Data Interoperability working group", "description": "This group includes the ontologies used by the RDA Wheat Data Interoperability working group.
"}' "$REST_URL/groups/WHEAT"

curl -X PUT -H "Content-Type: application/json" -H "Authorization: apikey token=$API_KEY" -d '{ "acronym": "RICE", "name": "Rice related ontologies", "description": "This group includes the ontologies used within the Computational Biology Institute of Montpellier project for rice related data annotation."}' "$REST_URL/groups/RICE"

curl -X PUT -H "Content-Type: application/json" -H "Authorization: apikey token=$API_KEY" -d '{ "acronym": "LOVINRA", "name": "INRA Linked Open Vocabularies", "description": "This group includes the ontologies and vocabularies produced or co-produced by INRA scientists."}' "$REST_URL/groups/LOVINRA"

curl -X PUT -H "Content-Type: application/json" -H "Authorization: apikey token=$API_KEY" -d '{ "acronym": "CROP", "name": "Crop Ontology Curation Tool", "description": "This group includes the ontologies that form the Crop Ontology and currently available within the cropontology.org platform."}' "$REST_URL/groups/CROP"


# Create categories
curl -X PUT -H "Content-Type: application/json" -H "Authorization: apikey token=$API_KEY" -d '{ "acronym": "Crop", "name": "Crop Ontology", "description": "This category includes all the ontologies of the crop ontology project."}' "$REST_URL/categories/Crop"

curl -X PUT -H "Content-Type: application/json" -H "Authorization: apikey token=$API_KEY" -d '{ "acronym": "Reference", "name": "Reference ontologies for plant", "description": "This category includes all the ontologies that are reference ontologie for plant or crop."}' "$REST_URL/categories/Reference"

curl -X PUT -H "Content-Type: application/json" -H "Authorization: apikey token=$API_KEY" -d '{ "acronym": "CO_010-089", "name": "010-089 General Germplasm", "description": "This category includes the general germplasm part of the crop ontology. Concepts from 010 to 089", "parentCategory": "Crop"}' "$REST_URL/categories/CO_010-089"

curl -X PUT -H "Content-Type: application/json" -H "Authorization: apikey token=$API_KEY" -d '{ "acronym": "CO_100-299", "name": "100-299 Plant Anatomy and Development", "description": "This category includes the anatomy and developement part of the crop ontology. Concepts from 100 to 299", "parentCategory": "Crop"}' "$REST_URL/categories/CO_100-299"

curl -X PUT -H "Content-Type: application/json" -H "Authorization: apikey token=$API_KEY" -d '{ "acronym": "CO_300-499", "name": "300-499 Phenotype and Trait", "description": "This category includes the phenotype and trait part of the crop ontology. Concepts from 300 to 499", "parentCategory": "Crop"}' "$REST_URL/categories/CO_300-499"

curl -X PUT -H "Content-Type: application/json" -H "Authorization: apikey token=$API_KEY" -d '{ "acronym": "CO_500-699", "name": "500-699 Structural and Functional Genomic", "description": "This category includes the structural and functional genomic part of the crop ontology. Concepts from 500 to 699", "parentCategory": "Crop"}' "$REST_URL/categories/CO_500-699"

curl -X PUT -H "Content-Type: application/json" -H "Authorization: apikey token=$API_KEY" -d '{ "acronym": "CO_700-799", "name": "700-799 Location and Environmental", "description": "This category includes the location and environmental part of the crop ontology. Concepts from 700 to 799", "parentCategory": "Crop"}' "$REST_URL/categories/CO_700-799"



