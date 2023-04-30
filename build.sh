#!/bin/bash

DIR=package
if [ -d "$DIR" ]; then
    rm -rf "$DIR"
fi

rm -f deployment-package.zip

pip install --target ./package -r requirements.txt
cd package
zip -r ../deployment-package.zip .
cd ..
zip deployment-package.zip lambda_function.py
zip deployment-package.zip handlers.py
zip deployment-package.zip chatgpt.py
zip deployment-package.zip facebook.py
zip deployment-package.zip constants.py