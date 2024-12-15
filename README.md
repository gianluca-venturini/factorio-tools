# Factorio belt placement
This is a Factorio maximum throughput belt balancer placement tool.
A maximum throughput belt balancer is a type of balancer that sends the same amount of input to every output, at the same time ensuring the maximum theoretical throughput.
This solver is only finding a balancer, if it exists, given the NxM grid size, it won't attempt to minimize the grid size.

To find the optimal solution it uses a combination of CP-SAT solver and optimization heuristics.

This is a toy project to teach myself how to iterate on problem solving using a MIP or CP-SAT solvers.

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

### Learnings
- Underground belts entrances can't be placed between entrance and exit

- Start with MIP model and SCIP
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
- balancer 4x4 is computationally infeasible with naiive MIP model and SCIP

- Adding feasibility mode rather than optimal solution only
- Discretizing continuous flow into integer flow
- Migrate to CP-SAT
- Modeling underground belts with underground flow is more efficient than modeling entrance/exit in a single variable
    - Migrated undeground representation to lower dimensionality and more constraints
- Used directly component variables in objective function (-16%)
    - before: 75s
    - after 63s
- use Hint with an order that reflects the likelyhood
    - 6x6 top 2 rows hidden
        - optimal
            - without: (90.8856)
            - hint: belts=1 (82.0006) -- better
            - hint: mixers=1 (85.1349) -- better
            - hint: underground=1 (80.5116) -- best?
            - hint: belts=1, mixers=1, underground=1 (82.0006) -- better
        - feasible
            - without (17.1655)
            - hint: belts=1 (7.08848) -- better
            - hint: mixers=1 (23.7942) -- worse
            - hint: underground=1 (19.2976) -- worse
            - hint: belts=1, mixers=0 (7.08848) -- better, but identical to previous
            - hint: belts=1, mixers=1, underground=1 (7.08848) -- better, identical
            - hint: belts=0, mixers=1, underground=0 (6.49246) -- best
            - DecisionStrategy belts=1, mixers=0, underground=0: (17.1655) -- identical because IDK how to use it
    - 6x6 top 2 rows hidden - no underground distance contraints
        - feasible
            - without (10.2252)
            - hint: all_d belts=1 (13.4252)
            - hint: all_d mixers=1 (17.905)
            - hint: up belts=1 (7.15802)
            - hint: up belts=1, mixer=1 (7.15802)
            - hint: up belts=1, mixer=1, underground=1 (7.15802)
    - 6x6 top 4 rows hidden
        - feasible
            - without (3787.97)
            - hint: belts=1 (1475.37) -- 
            - hint: mixers=1 (767.999) -- best for some reason
            - hint: belts=1, mixers=1, underground=1 (1475.37) -- 
            - hint: belts=1, mixers=0, underground=0 (1475.37) -- 
            - hint: belts=0, mixers=1, underground=0 (767.999) --

- Supplying pre-solved network increases performance drastically



## Notable solutions
- 4x4 balancer
```
↥↿↾↥
‧↥↥△
△▶▶▲
↿↾‧‧
↥▲◀◀
△△△▲
↿↾↿↾
```

- 6x6 balancer on 8x9 grid feasible in 3min
```
↿↾↿↾↿↾‧‧
↥↥↥↿↾↥‧‧
‧‧‧↥↥△‧‧
△‧△▶▶▲‧‧
▲↤↿↾▶▼◁◀
▶▶▲↿↾⇃⇂▲
↥△▶▲▲◀▶▲
△↿↾△△↿↾‧
↿↾↿↾↿↾‧‧
```

- 8x8 balancer on 8x10 grid feasible in 30min
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

- new underground belt design in 15min
```
↿↾↿↾↿↾↿↾
↥↥↥▲↥↥↥▲
‧▶▷▲◀◀↦▲
△▲◀‧△▲◀◀
▲↤▲▶▲◁◀▲
‧‧↿↾‧‧↿↾
▶▶▲↥▶▶▲↥
↥△△‧↥△△‧
△↿↾△△↿↾△
↿↾↿↾↿↾↿↾
```

- with feasible solution fixing two rows and 2 cells finds solution in 83s
- with feasible solution fixing two rows and 2 cells and hint to uf=0 finds solution in 17s (7.85157)
    - hint belts -- worse
    - hint mixers

- with pre-computed graph feasible solution no fixed rows in 70s
- found 16x16 with hints, symmetry breaking in 1:30h
- found 16x16 with hints, symmetry breaking and objective function in 55min
hints
```
↿↾↿↾↿↾↿↾↿↾↿↾↿↾↿↾
▲▲▲▲▲▲▲▲▲▲▲‧‧▲▲▲
‧‧‧‧‧‧‧‧‧‧‧‧‧‧‧‧
‧‧‧‧‧‧‧‧‧‧‧‧‧‧‧‧
‧‧‧‧‧‧‧‧‧‧‧‧‧‧‧‧
‧‧‧‧‧‧‧‧‧‧‧‧‧‧‧‧
‧‧‧‧‧‧‧‧‧‧‧‧‧‧‧‧
‧‧‧‧‧‧‧‧‧‧‧‧‧‧‧‧
‧‧‧‧‧‧‧‧‧‧‧‧‧‧‧‧
‧‧‧‧‧‧‧‧‧‧‧‧‧‧‧‧
‧‧‧‧‧‧‧‧‧‧‧‧‧‧‧‧
▲‧↿↾↿↾‧‧‧‧↿↾↿↾‧‧
▶▶▲▲▲▲◀◀▶▶▲▲▲▲◀◀
▲△△▲▲△△▲▲△△▲▲△△▲
▲↿↾▲▲↿↾▲▲↿↾▲▲↿↾▲
↿↾↿↾↿↾↿↾↿↾↿↾↿↾↿↾
```

```
↿↾↿↾↿↾↿↾↿↾↿↾↿↾↿↾
▲▲▲▲▲▲▲▲▲▲▲↥↥▲▲▲
▲▲↥↥▲↿↾↿↾▲▲◀◀▲↥↥
▲▲↤‧▲↥↥↥↥▲◁↤↿↾◁◀
▲▶▷‧▲◀◀◀↦▲‧▶▲▲△▲
↿↾△‧▶▷‧▲↼◀◀▲↦▲↿↾
↥↥▲↤▲△△◁↽↤↥▲◁◀↥▲
‧‧▶▷▲↥▲◀◀◀↦▲‧↥▶▲
▶▷↥‧▲◀◀△↦▲▶▶▶▶▲△
▲◀◀△▶▷↥▲◀◀▲△△‧↦▲
△‧▲↿↾▶▶▼△↥▲↿↾▶▶▼
▲↤↿↾↿↾◁◀▲↤↿↾↿↾◁◀
▶▶▲▲▲▲◀◀▶▶▲▲▲▲◀◀
▲△△▲▲△△▲▲△△▲▲△△▲
▲↿↾▲▲↿↾▲▲↿↾▲▲↿↾▲
↿↾↿↾↿↾↿↾↿↾↿↾↿↾↿↾
```