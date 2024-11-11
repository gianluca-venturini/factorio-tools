## Install dependencies
pyenv install 3.9.13
pyenv global 3.9.13
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

## Run tests
python -m unittest discover -p '*_test.py'

## Convert blueprints
echo "my_base64_string_without_first_byte" | base64 -D | zlib-flate -uncompress

### TODO
- Check that blueprints are rendered correctly
- Make sure underground belts don't overlap
- Write tests for underground belts