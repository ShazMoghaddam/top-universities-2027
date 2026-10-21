# Fonts

`InterNum.woff2` is [Inter 4](https://rsms.me/inter/) (SIL Open Font License, see `OFL.txt`) with its tabular figures (`tnum`) and open digits (`ss01`) made the default shapes. `build.py` uses it for every number in the carousel.

Turning those features on in CSS gives the same look, but Chromium then writes the numbers into the PDF in a way that copies, searches and reads aloud as gibberish. With the features built in, the PDF text is clean.

To remake it (macOS):

```bash
pip install opentype-feature-freezer fonttools brotli
# InterVariable.ttf from the Inter release on GitHub (rsms/inter)
pyftfeatfreeze -f 'tnum,ss01' -S -U Num InterVariable.ttf InterNum.ttf
pyftsubset InterNum.ttf --unicodes="U+0020-007E,U+00A0-00FF,U+2013,U+2014,U+2018,U+2019,U+201C,U+201D,U+2022,U+2026,U+2212" \
  --layout-features='*' --flavor=woff2 --output-file=InterNum.woff2
```
