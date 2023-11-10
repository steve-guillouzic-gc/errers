# SPDX-FileCopyrightText: 2023 His Majesty in Right of Canada
#
# SPDX-License-Identifier: LicenseRef-MIT-DND
#
# This file is part of the ERRERS package.

.PHONY: default all purge

SHELL := /bin/bash

output := errers.ico errers32.png errers.icns

default: all
all: $(output)

errers.ico:
	convert errers.png -define icon:auto-resize errers.ico

errers32.png:
	convert errers.png -resize 32 errers32.png

errers.icns:
	png2icns errers.icns errers.png

purge:
	rm $(output)
