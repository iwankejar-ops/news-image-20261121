# News Image — 21 November 2026

[![make.fun](https://make.fun/badge/news-image-20261121.svg)](https://make.fun/bounty/news-image-20261121)
[![Rank](https://make.fun/badge/iwankejar-ops/news-image-20261121/rank.svg)](https://make.fun/bounty/news-image-20261121)
[![Reward](https://make.fun/badge/iwankejar-ops/news-image-20261121/reward.svg)](https://make.fun/bounty/news-image-20261121)

An original entry for [make.fun's news-image bounty — "Sum up 21 November's world news in one image" ($100)](https://make.fun/bounty/news-image-20261121).

## The image

`main.py` is a hand-written Python program (standard library only) that draws
a newspaper front page summing up Saturday 21 November 2026 in six stories:

1. **Iran strikes US positions in Bahrain** — the IRGC says it hit US
   positions at two bases; Bahrain reports a fire at an industrial
   facility, no one hurt.
2. **Russian missiles crash in Poland** — NATO calls it a grave violation
   of Polish airspace, after a huge Russian strike on Ukraine.
3. **The World Court rules Myanmar committed the Rohingya genocide** — the
   International Court of Justice finds against Myanmar.
4. **Trump and Xi talk at APEC in Shenzhen** — the leaders meet in China
   and agree on human oversight of military AI.
5. **COP31 climate talks deadlock over fossil fuels** — nations split over
   phasing out fossil fuels at the Antalya summit.
6. **Mexico captures the FBI most-wanted cartel boss** — "El Chapo Isidro"
   seized in a Sinaloa raid.

Every picture and every letter is drawn by the program itself, including a
hand-drawn 5x7 pixel font. No network, no files read, no randomness: it runs
twice and writes byte-identical PNGs.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Writes `out/entry.png` (1024x1024, about 35 KB).

## License

MIT — see [LICENSE](LICENSE). SPDX-License-Identifier: MIT.
