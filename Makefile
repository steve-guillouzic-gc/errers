# SPDX-FileCopyrightText: 2023 His Majesty in Right of Canada
#
# SPDX-License-Identifier: LicenseRef-MIT-DND
#
# This file is part of the ERRERS package.

.PHONY: build clean default help licenses purge version

SHELL := /bin/bash
PYTHON := python3

# Interrupt if not working on a Git repository
git_status := $(if $(shell git status), 'Ok', \
                   $(error Makefile requires Git repository))

# Files in repository
files := $(shell git ls-files)
files := $(if $(files), $(files), $(error Empty Git repository))

# Build version string for ERRERS using information returned by "git describe"
version_list := $(subst -, ,$(shell git describe --dirty))
version_list := $(if $(version_list), $(version_list), \
                     $(error Missing Git tag))
version_public := $(word 1,$(version_list))
ifeq ($(words $(version_list)),1)
	# 1 version element:
	#     - Tagged commit with no further changes
	#     - Use only public version identifier
	version_python := $(version_public)
else
	# 2+ version elements:
	#     - Tagged commit with additional changes
	#     - Use public and local version identifiers
	ifeq ($(words $(version_list)),2)
		# 2 elements: only uncommitted changes
		dirty := $(word 2,$(version_list))
		version_local := $(dirty)
	else
		# 3+ elements: has committed changes
		n_commits := $(word 2,$(version_list))
		hash := $(subst g,,$(word 3,$(version_list)))
		version_local := $(n_commits).git.$(hash)
		ifeq ($(words $(version_list)),4)
			# 4 elements: also has uncommitted changes
			dirty := $(word 4,$(version_list))
			version_local := $(version_local).$(dirty)
		endif
	endif
	version_python := $(version_public)+$(version_local)
endif

# Stem for package names
stem := errers-$(version_python)

# Help text
define HELP
usage: make [TARGET]

Targets:
    archive: generate archive of repository files in their local state
    build (default): generate distribution packages after generating
        LICENSES.txt and setting version number
    clean: delete temporary files, except archive, distribution packages, 
        and _version.py
    licenses: generate LICENSES.txt file
    purge: delete all temporary files
    version: set version number from Git repository
endef

default: build

LICENSES.txt: $(files)
	reuse lint || (echo 'Creation of SPDX file interrupted.' && exit 1)
	reuse spdx >LICENSES.txt

src/errers/_version.py: $(files)
	cp templates/_version.py src/errers
	sed -i -e "s/VERSION/'$(version_python)'/" src/errers/_version.py

archive: $(files)
	zip errers-$(version_python)-archive.zip `git ls-files`

build: $(files) LICENSES.txt src/errers/_version.py
	$(PYTHON) -m venv --clear venv
	source venv/bin/activate; pwd
	source venv/bin/activate; $(PYTHON) -m pip install --upgrade pip
	source venv/bin/activate; $(PYTHON) -m pip install --upgrade setuptools
	source venv/bin/activate; $(PYTHON) -m pip install --upgrade wheel
	source venv/bin/activate; $(PYTHON) -m pip install --upgrade build
	source venv/bin/activate; $(PYTHON) -m build
	cd dist; tar -xzf $(stem).tar.gz
	cd dist/$(stem); zip -r ../$(stem).zip .
	rm -r dist/$(stem)

clean:
	rm -rf venv
	rm -rf `find . -name __pycache__`
	rm -rf LICENSES.txt src/errers.egg-info

help:
	$(info $(HELP))

licenses: LICENSES.txt

purge: clean
	rm -rf src/errers/_version.py dist *.zip

version: src/errers/_version.py
