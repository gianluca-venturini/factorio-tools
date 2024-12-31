# Factorio belt placement
This is a Factorio maximum throughput belt balancer placement tool.
A maximum throughput belt balancer is a type of balancer that sends the same amount of input to every output, at the same time ensuring the maximum theoretical throughput.
This solver is only finding a balancer, if it exists, given the NxM grid size, it won't attempt to minimize the grid size.

To find the optimal solution it uses a combination of CP-SAT solver and optimization heuristics.

This is a toy project to teach myself how to iterate on problem solving using a MIP or CP-SAT solvers.

Features implemented are:
- Define input and output flows on specific cells and set the 2D grid size.
- Provide fine grain controls: you can fix any component on the 2D grid using the `solution`.
- Supports optional pre-calculated Banes Network with `solution_network` variable.

## Install dependencies

```
pyenv install 3.9.13
pyenv global 3.9.13
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run tests

```
python -m unittest discover -p '*_test.py'
```

## Create balancer

Define the balancer in `balancer.py` inside the `BALANCERS` object. Use the balancer name as object key e.g. 4x4. In order to define the balancer design (e.g. grid size, where input and outputs are on the grid) you'll need to pass parameters to `solve_factorio_belt_balancer()` function.
Find a solution, if it exists, with e.g. 

```
python ft.py --solve_balancer=4x4
```

## Decode blueprints

```
echo "my_base64_string_without_first_byte" | base64 -D | zlib-flate -uncompress
```

### Learnings
[I wrote a blog post about it](https://gianlucaventurini.com/posts/2024/factorio-tools)

## Notable solutions

- 3x3 balancer
```
‧↥↿↾‧
▶▶▲↥‧
▲△▶▶▼
▲↿↾△▼
▲▲↿↾▼
↿↾▲▲◀
```

```
0eJydltmOgyAUhl+l4dpOZOnmZV9jMploe9KQUCSAE5vGdx/UprNAA3hlkHO+s/Gjd9SIDpTm0qLqjriFK6p+vSuQqBsQ7t0RhF01tajlCfTKbfBTKw2q3u/I8Iusxehvbwqc7YQpkKyv48rqWhrVart2JIsG5yrP0KMKDx8FAmm55TCTpsXtU3bXBrQzeDKgVxqMWXfOU190654zrUCqNQ7QyjF+P/ncUFW6KI9k2s6qbjQ8cw2n2dJte8GIF8wowa11e14Q8rZ5holgqYf91w8PXk5o/BdNAmiWjcap6E02moTQoYZsFwyVPuGZQ90t7D6J17FffDjJTx1cJpVxWDgOEp80LrPZNJntCzjGZiE2C7F9vaaNlsZHi33Rvr4L8OMuSOH6ik09+zT7zOB8DbNQIcHm+yJOaz5LaFK+ZnEy2xdt/JJP4eYLlIXYoV4TX6Cvcy4fOW/iOZN8cZJkdr44aTI7/4vKQuzt+PfxBdrM19ces92B7LaUMUrKYfgGVN8VJw==
```

- 4x4 balancer
```
↿↾↿↾
▲↿↾▲
▲↥↥▲
▲◀◀▲
‧‧↿↾
▶▶▲▲
▲△△▲
```

```
0eJydlttuwyAMhl+l4jqdCiRpl8u9xjRNSWtVSJQgIFOrKu8+p+m6A5licoXA8Nmx+U2urNEdWKdMYNWVqQAnVv1Yy5iuG9C49gI6rJpa12YPboUGtW+NZ9XrlXl1NLUezoeLBdx7w2TM1KdhFlxtvG1dWCMpsB6PmgOcWcX7t4yBCSooGEm3yeXddKcGHG54MOBsHXi/9larENCWMdt6PNiawS/CNk9Fxi44Iv+gHOxHG04jrEjACjpWRtg/Xx7HfEPzeXSeEDG/R0zAFskRSyq6XJgMMY/eRugO75M7uhbHf+D8Ab9f0bYLths2zjjbLXAmljp7XlgPQtL4ZmFBJIEd63SOzafY5RQ7FuscW5DZ6YqV5JykSParyeQEbrpmxzoWv9liip0uWk5mx6ql1bEg5CQWKa2OFHa6Jsd8l4R3KNYktZOV381FGVJvEbFIqZ1sgbN01crprOEfwgc4P96rHc+3z2JbyjyXYtP3nwBV9c4=
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

Blueprint
```
0eJydmNtuozAQQH+l8jNdgW9cHvsbq6oiqVUhEYPArBpF+fc6IULbeBLP+CkiwLFn7OOxObFdv5hx6qxjzYl1zhxY899/Gevbnen9f2+mdy+7tm/t3kwv/ka3H+zMmr8nNndftu0v77vjaPyzV0zGbHu4XLmptfM4TO7Vkxw7+1ftp/lmTXF+z5ixrnOdWUnXi+OHXQ47M/kHNob5Hiczz6/z2HfO+XsZG4fZvzjYS7sexv+ojB1Zk3v+ZzeZ/XrPXwZYTsBKPFYQsBqPlQH2LqEBvLiii99oDqAVGc0hNNRrTUiGuCUDgS3JPUajqwC9+Gk6fU2D/30A1xv8NvOHxY3L5cFIY3VCY2VqY0WeOIV4PGtF6Gg8Er7Rn0SiodZCdWORCHQkob/xSCQmErA1utYKHQndaw2xwREIxY6xSzQ7tDs+AtX9CHQWN5VC32OB1OhAQr1xC6uIr9mcLrOA2GBhDGXGDS6GTVe3gthQvnmoLm4sMf2mi5pf2fI3W0LsUNT4hC82OnHx5KG62KU60hqYtxSZ5X1rSJk5XWYFDRLITq/VzwMB95B0uysoEJBNt7tGs+l2r5aouCWCbneBZtPt5hAbmjiCXoYFxIaqgEhxWW70x5MSbCx1160QEyd9262eL0pgJPTCXGIjkanqYtip6mLYlONwfjuq6bhaknIe5jAX7G/qzhnDDpV93OeK0Gf6rnldHktEnul2FhAb8kXS6yqH2GBO6C4KLFvRXVRodsqJV2902n5A0etqiR1cRa+rFTpJdElrNJteV1eZKkROUupqsdFpdVWlbJE5ojEwa3SVBZQ1kJ2yRZaJgejQ7cdrtLqt0YggdOrhF8MONcZ+2ajouxydehzGRBKKHa/qNYJLqbySwKV8iNaPuO8Z+2emec14Vciy5qUWUgqen88/jQ+Q6Q==
```

- 8x8 balancer on 8x10
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

```
0eJydmNtu4jAQhl+l8nW6IrZjA5f7GqtqFahVWQpO5DirIsS7ryEVexgLz8xVFJJ8P3P4fbqIw7C4KfqQxP4ifHInsf/rt0YM/cEN+bfvbkgvh37ow9HFl/zAH8cwi/2Pi5j9R+iH2/fpPLn87h3TiNCfbncp9mGexpheMymJa/40vLtPsW+vb41wIfnk3Uq635x/huV0cDG/8GC4zym6eX6dp8GnlJ81Yhrn/OEYbroZtvnWNeKcr5n/7qM7rs/yLcBKAlbisYqA1XisJmANHtsB7JKrEj/imK9rpWCO7/A2w78KPS5pWm4vVsQMQ6zlilmGmOSKbYHYf+0OpNRDqoLeMeLQ3DjaDUOtY6tBZ9fVDFsNGr5WJIstUgtdX2OvjS3/ZcsSG1of28nyT5Z8AEkqisEBAdfJEpEk6P8aW5fYpsSGdq+xOzQbuhvbpvJ5mxYrAA2Pa1NEBSTH3utwr562UlEMuhvnCYUIhO5lWWKXyi2hl7EjLiNJ0Ny4vsUkie5lg04S3csWzaZ7ee1RjcgJx8vtg/7Ey8VI6F6W2EgU9DJupNb1KUfRravR/xtaF7vE0E/tVSqAos/LphRIkU23rkUnCVq3vjnpEFxo2/o2AsPlWtYgmpG+uG7RbK5BTT0nmjPZqgeduLrVXMsisqTps22HZnMdiqkAZ+Vs2RXg76UtQ42/mbbkVYrmb6YZYpwpWrPzyNlfd8zQOs6QYLhinN312o9buhjlNK39mli2iPMpzmJccYPgjBeaK0aZ4jtCxjgDg+UGAQeG+tnsDhEEHAPq6x8MF7q9fjqL4Bpo7Pq6CnDfGvHLxXmdK7ettjtpjdJayc31+hsxzQHI
```

- 16x16 balancer on 16x16

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

```
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
```


### Blog post notes
Measurements in the blog post table are made on these commits

CP-SAT: 82d9734faa62195a59941d9318516266bbca50ba
CP-SAT Banes Networks: 8637ff8d38e5acb2f1e62b2c5040aa65bd44b946
CP-SAT Banes Networks, direction optimized: 81cd1a99820d1af18321359722dd461f16437d98

ffmpeg -i 3_3.mov -t 1 -vf "fps=40,scale=640:-1:flags=lanczos" -c:v libwebp -compression_level 6 -q:v 20 -loop 0 3_3-2.webp