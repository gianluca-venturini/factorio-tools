## Install dependencies
pyenv install 3.11.0
pyenv global 3.11.0
python -m venv .venv
source .venv/bin/activate

## Run tests
python -m unittest discover -p '*_test.py'

## Convert blueprints
echo "my_base64_string_without_first_byte" | base64 -D | zlib-flate -uncompress

