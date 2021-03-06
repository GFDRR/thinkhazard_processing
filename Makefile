PY_FILES = $(shell find thinkhazard_processing -type f -name '*.py' 2> /dev/null)
DATA = world

.PHONY: all
all: help

.PHONY: help
help:
	@echo "Usage: make <target>"
	@echo
	@echo "Possible targets:"
	@echo
	@echo "- install                 Install thinkhazard"
	@echo "- initdb                  Initialize database"
	@echo "- populatedb              Populates database. Use DATA=turkey if you want to work with a sample data set"
	@echo "- import_admindivs        Import administrative divisions. Use DATA=turkey or DATA=indonesia if you want to work with a sample data set"
	@echo "- import_recommendations  Import recommendations"
	@echo "- import_furtherresources Import further resources"
	@echo "- check                   Check the code with flake8"
	@echo "- test                    Run the unit tests"
	@echo "- harvest                 Harvest GeoNode layers metadata"
	@echo "- download                Download raster data from GeoNode"
	@echo "- complete                Mark complete hazardsets as such"
	@echo "- process                 Compute hazard levels from hazardsets for administrative divisions level 2"
	@echo "- decisiontree            Run the decision tree and perform upscaling"
	@echo

.PHONY: install
install: .build/requirements.timestamp

.PHONY: initdb
initdb: .build/requirements.timestamp
	.build/venv/bin/initialize_db

.PHONY: populatedb
populatedb: initdb import_admindivs import_recommendations import_furtherresources

.PHONY: import_admindivs
import_admindivs: .build/requirements.timestamp
	wget -nc "http://dev.camptocamp.com/files/thinkhazard/$(DATA)/g2015_2014_0.sql.zip"
	unzip -o g2015_2014_0.sql.zip
	wget -nc "http://dev.camptocamp.com/files/thinkhazard/$(DATA)/g2015_2014_1.sql.zip"
	unzip -o g2015_2014_1.sql.zip
	wget -nc "http://dev.camptocamp.com/files/thinkhazard/$(DATA)/g2015_2014_2.sql.zip"
	unzip -o g2015_2014_2.sql.zip
	.build/venv/bin/import_admindivs
	rm -rf g2015_2014_*

.PHONY: import_recommendations
import_recommendations: .build/requirements.timestamp
	.build/venv/bin/import_recommendations

.PHONY: import_furtherresources
import_furtherresources: .build/requirements.timestamp
	.build/venv/bin/import_further_resources

.PHONY: harvest
harvest: .build/requirements.timestamp
	.build/venv/bin/harvest

.PHONY: download
download: .build/requirements.timestamp
	.build/venv/bin/download

.PHONY: complete
complete: .build/requirements.timestamp
	.build/venv/bin/complete

.PHONY: process
process: .build/requirements.timestamp
	.build/venv/bin/process

.PHONY: dt
dt: .build/requirements.timestamp
	.build/venv/bin/decision_tree

.PHONY: decisiontree
decisiontree: .build/requirements.timestamp
	.build/venv/bin/decision_tree

.PHONY: check
check: flake8

.PHONY: flake8
flake8: .build/dev-requirements.timestamp .build/flake8.timestamp

.PHONY: test
test: .build/dev-requirements.timestamp
	.build/venv/bin/nosetests

.build/venv:
	mkdir -p $(dir $@)
	# make a first virtualenv to get a recent version of virtualenv
	virtualenv venv
	venv/bin/pip install virtualenv
	venv/bin/virtualenv .build/venv
	# remove the temporary virtualenv
	rm -rf venv

.build/dev-requirements.timestamp: .build/venv dev-requirements.txt
	mkdir -p $(dir $@)
	.build/venv/bin/pip install -r dev-requirements.txt > /dev/null 2>&1
	touch $@

.build/requirements.timestamp: .build/venv setup.py requirements.txt
	mkdir -p $(dir $@)
	.build/venv/bin/pip install numpy==1.10.1
	.build/venv/bin/pip install -r requirements.txt
	touch $@

.build/flake8.timestamp: $(PY_FILES)
	mkdir -p $(dir $@)
	.build/venv/bin/flake8 $?
	touch $@

.PHONY: clean
clean:
	rm -f .build/flake8.timestamp

.PHONY: cleanall
cleanall:
	rm -rf .build
