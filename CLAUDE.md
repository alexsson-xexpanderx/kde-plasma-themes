# Retrograde — notes for working on this theme

Everything under `theme/` is generated. Edit `src/`, then `python3 src/build.py`
(or one part: `colors aurorae plasma wallpaper lookandfeel cursors extras`).
All colours come from `src/palette.py`. The only hand-made files in `theme/`
are the screenshots in `plasma/look-and-feel/Retrograde/contents/previews/`,
which `build_lookandfeel.py` keeps across rebuilds.

## Testing without touching the real desktop

The user runs their own Plasma session and conkies. Never apply the theme to
it, never restart plasmashell or kwin, and never `pkill conky`.

Test in a throwaway session instead:

- `Xvfb :91 -screen 0 2560x1440x24 +extension GLX`, then
  `dbus-run-session` around `kwin_x11 --replace` and `plasmashell`.
- Fake `HOME`, `XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `XDG_CACHE_HOME` under the
  scratchpad. `XDG_CONFIG_DIRS` must be `<fake config>/kdedefaults:/etc/xdg`:
  Plasma 6 writes a global theme's choices to `kdedefaults`, and without it on
  the path the decoration silently falls back to Breeze.
- `XDG_RUNTIME_DIR` needs a short path, or KIO cannot create its sockets.
- Any KDE tool (`plasma-apply-*`, `qdbus6`, `kwriteconfig6`) must run with the
  fake session's `DBUS_SESSION_BUS_ADDRESS`, never the real one.
- Screenshot with `import -window root`; move windows with a KWin script
  through `/Scripting`; clicks via XTest (`libXtst`) since there is no xdotool.
- Stop it by killing the `dbus-run-session` process tree and the Xvfb pid you
  started, nothing matched by name.

## Things that are easy to get wrong

- Aurorae and KSvg read element names, not files: `decoration-topleft`,
  `active-center`, `hint-top-margin` and so on. Breeze's SVGs in
  `/usr/share/plasma/desktoptheme/default/` are the reference for names.
- KSvg sizes an element by its bounding box, so every group carries a
  near-transparent placeholder rect (see `svgkit.py`).
- The user's display is scaled to 115%. Pixel art drawn as rows of abutting
  rects comes out see-through along every seam at a fractional scale, so draw
  grids with `Group.grid()` / `Group.pixels()`, which lay a solid underlay
  beneath. Check with Qt's `QSvgRenderer` at 1.15: solid areas must be alpha
  255, and at 1.0 the output must not change.
- Popup headings (`plasmoidheading`) are stretched to the popup's own edges;
  they keep their top rows and side columns clear so the sunset stripe and the
  outline show.
- Cursors are a 12 px grid so 24/36/48/60/72/96 scale by whole numbers.
- Icons (`build_icons.py`, art in `icons_art.py`) convert the user's installed
  candy-icons; the build needs it at `~/.local/share/icons/candy-icons`.
  KIconLoader tries a name's shorter forms in this theme before Breeze Dark,
  so a name added here can hide Breeze icons; `protect_breeze` ships those, and
  `kiconfinder6` with a fake `XDG_CONFIG_HOME`/`XDG_DATA_DIRS` shows what a
  name resolves to. Never draw toolbar actions (`breeze_actions`). The build
  also converts this machine's installed apps' icons into `theme/`: the user
  wants everything Retrograde in the repository, not only in `~/.local/share`.
- The wallpaper keeps the middle and the right edge calm for Conky Orrery
  (centred) and conky-dashboard (right edge), and keeps the sunset low enough
  that the Orrery's bottom readouts stay on dark sky.

## Extras

`extras/conky-orrery-pixel` and `extras/conky-dashboard-pixel` are copies of
the user's conkies (from ~/git/Conky-themes/Conky_Orrery and
~/git/conky-dashboard), changed to draw shapes on a small canvas and text at
full resolution on top. Change the copies, never the originals.

The dashboard copy holds **no API key**: it falls back to the original's
`.owm_key`. Never copy or symlink the key into this folder. When testing the
dashboard, render a scratch copy with `refresh_updates`/`refresh_weather` set
to 0, or the first frame fetches weather and runs the update checks.
