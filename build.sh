#!/bin/bash

DIR=package
if [ -d "$DIR" ]; then
    echo "*** deleting package folder"
    rm -rf "$DIR"
fi

echo "*** deleting zip file"
rm -f deployment-package.zip

echo "*** installing dependencies"
poetry install --without dev --sync
cd .venv/lib/python3.11/site-packages
zip -r ../../../../deployment-package.zip .
cd ../../../../
zip -r deployment-package.zip src
zip deployment-package.zip lambda_function.py