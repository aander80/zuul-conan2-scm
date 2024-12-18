#!/bin/sh

./setup.sh

./.venv/bin/python create_change.py conan-repo "My change"
