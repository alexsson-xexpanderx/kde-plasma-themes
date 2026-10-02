# Conky Orrery, pixel edition

A copy of [Conky Orrery](https://github.com/alexsson-xexpanderx/Conky-themes)
drawn as pixel art, to sit on the Retrograde wallpaper.

![The pixel Orrery on the Retrograde wallpaper](../../screenshots/conky-orrery-pixel.png)

Everything the original shows is still there and still moves the same way.
What changes is how it is drawn:

- The hoops, ticks, cores, glows and readout arcs are drawn on a canvas four
  times smaller than the window, with antialiasing off, and enlarged with hard
  edges. One pixel of the widget is one pixel of the wallpaper's art.
- Each core is a small plus-shaped sprite that moves a whole pixel at a time,
  and its glow is rings of pixels, each a step fainter.
- The writing is not pixelated. The clock, the hoop labels and the readouts
  are drawn afterwards at full resolution, on top, so they stay sharp.
- The colours follow the sun it hangs over: today's month, day and weekday in
  the gold of the sun's core, the readouts in the pink of the sky round it,
  and mauve for the date hoops and the cores, the violet higher up. The
  readouts are drawn strongly, at 0.85: gold or pink much fainter than that
  mixes with the violet sky into khaki or brown.
- The seconds hoop is the clock's white, and only the minute so far is drawn
  of it: the arc from the top of the minute round to the moving head. The rest
  of the ring and its ticks are left out, so it stands apart from the three
  date hoops as part of the time.
- Today's month, day and weekday are written at one size, and do not shrink on
  the far side of their hoop. In the original each hoop sizes its own label,
  which left the day number the smallest of the three.

**Run it:**

```bash
conky -c ~/git/kde-plasma-themes/extras/conky-orrery-pixel/start_conky_orrery
```

It sits in the same place as the original, so stop that one first. If you
start the Orrery at login, point the autostart entry at this folder's
`start_conky_orrery` instead.

**Change the colours:** `./orrery_colors.py` works as it does for the
original. Its **Apply and restart conky** restarts only this copy and leaves
the original alone.

## Pixel size

`pixel_size` at the top of `lua_orrery.lua`, in screen pixels. The wallpaper is
painted about 360 art pixels tall whatever the screen, so the match is your
screen height divided by 360:

| Screen height | `pixel_size` |
|---|---|
| 768 or 800 | 2 |
| 1080 | 3 |
| 1440 | 4 |
| 2160 | 6 |

`1` turns the pixel look off and draws it smooth, like the original.

## What it gives up

In the original the clock and the labels are sorted by depth along with
everything else, so the near half of a hoop or of the cage can pass in front of
the numerals. Here the text is always on top, because it is drawn after the
pixel canvas. That is the price of keeping it sharp.

## Where it came from

`lua_orrery.lua`, `orrery_colors.py`, `orrery_preview.lua` and
`start_conky_orrery` are copied from Conky_Orrery and changed only as above. The
pixel drawing is the `PIXELS` section of `lua_orrery.lua`. The original's
README covers everything else.
