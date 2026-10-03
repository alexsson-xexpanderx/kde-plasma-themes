# Conky Orrery, pixel edition

A pixel-art copy of [Conky Orrery](https://github.com/alexsson-xexpanderx/Conky-themes)
for the Retrograde theme.

![Orrery](../../screenshots/conky-orrery-pixel.png)

## Run

```bash
conky -c ~/git/kde-plasma-themes/Retrograde/extras/conky-orrery-pixel/start_conky_orrery
```

Stop the original first, since they sit in the same spot.

## Settings

At the top of `lua_orrery.lua`:

- `pixel_size`: your screen height divided by 360 (4 at 1440p, 3 at 1080p)
- `font_name` and `font_em`: the font and its pixel size (0 for a normal font)

To change the colours, run `./orrery_colors.py`.
