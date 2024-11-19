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

### Learnings
- Underground belts entrances can't be placed between entrance and exit


## Performance improvements
- Inverting two flows
    - Optimal solution is 13.
    - with occupied cell variabe: 1m 3s
```
solve_factorio_belt_balancer((5, 6), 2, [
    (2, 0, 'S', 0, 1),
    (3, 0, 'S', 1, 1),
    (3, 5, 'N', 0, -1),
    (2, 5, 'N', 1, -1),
])
```

- Adding feasibility mode rather than optimal solution only
- Discretizing continuous flow into integer flow
- Migrate to CP-SAT


## Notable solutions
- 6x6 balancer on 8x9 grid
```
‧‧↿↾↿↾↿↾
‧‧▲↿↾↥↥▲
▶▷▲↥↥‧↦▲
↥‧▲◀◀△‧‧
‧‧▼◀↿↾‧‧
△⇃⇂↿↾▲◀◀
▲◀▶▲▲◀△↥
‧↿↾△△↿↾△
‧‧↿↾↿↾↿↾
```

- 8x8 balancer on 8x10 grid
```
↿↾↿↾↿↾↿↾
↥↥▲↥↥↥↥↥
‧‧▲◀◀△‧△
‧▶▷‧↿↾↦▲
△▲◀‧▲▲◀◀
▲↤↥‧▲◁◀↥
▶▶▶▶▲▶▲‧
↥△△△△▲△‧
△↿↾↿↾↿↾△
↿↾↿↾↿↾↿↾
```