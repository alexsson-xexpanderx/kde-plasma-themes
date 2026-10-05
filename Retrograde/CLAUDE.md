# Retrograde — notes for working on this theme

Everything under `theme/` is generated. Edit `src/`, then `python3 src/build.py`
(or one part: `colors aurorae plasma wallpaper lookandfeel cursors icons fonts
sddm extras`).
All colours come from `src/palette.py`. The only hand-made files in `theme/`
are the screenshots in `plasma/look-and-feel/Retrograde/contents/previews/`
and `sddm/Retrograde/preview.png`, which the builds keep across rebuilds.

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
- The user's desktop is Wayland at 115% with Aurorae's v2 engine
  (`library=org.kde.kwin.aurorae.v2` in their kwinrc). To see the decoration
  as they do, run `kwin_wayland --x11-display :91 --scale 1.15 --socket wl91
  "<app>"` inside `dbus-run-session` on the Xvfb, with that kwinrc in the fake
  config and the theme in the fake `XDG_DATA_HOME/aurorae/themes`. Set its
  output scale in a `kwinoutputconfig.json` in the fake config (`--scale`
  only enlarges the host window), and set `XDG_CURRENT_DESKTOP=KDE` or apps
  ignore `kdeglobals`. Slackware's fontconfig reads `~/.local/share/fonts`
  through `HOME`, not `XDG_DATA_HOME`, so put fonts under the fake home.

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
- Aurorae v2 does not take `BorderLeft`/`BorderRight`/`BorderBottom` as given:
  it clamps them to the border size setting (4 to 6 px at Normal), so the
  frame is drawn solid behind the window, or the wallpaper shows between its
  edge and the window. The frame is one colour with no outline and no shadow
  (padding 0): the user rejected both. At 115% a 1-px outline blends with the
  wallpaper, and v2 turns padding into a shadow image made at 100% and
  stretched, which looked see-through and left lines on the wallpaper as
  windows moved.
- Popup headings (`plasmoidheading`) are stretched to the popup's own edges;
  they keep their top rows and side columns clear so the sunset stripe and the
  outline show.
- Cursors are a 12 px grid so 24/36/48/60/72/96 scale by whole numbers.
- Icons (`build_icons.py`) are solid sprites: folders and pages in
  `icons_art.py` (the user is happy with these; leave them alone), apps and
  the rest designed from shapes in `icons_apps.py` with the kit in
  `icons_draw.py`, and the remainder converted from Breeze's coloured icons
  and installed apps' own. Never base them on thin-line sets like candy-icons:
  the user rejected that look. Brand logos come from the installed app's own
  logo (`icons_apps.BRANDS` only stand in when it is missing): a logo drawn
  from shapes did not read as the brand. Centre designs on x = 12 with
  even-width symbols, or they sit half a cell off at one of the two sizes.
  The converter must not average colours per cell (the user saw that as
  artifacts): it reduces a logo to 16 colours at 8x, votes per cell on the
  theme colour, decides ramps per hue group so gradients never split, merges
  shades under 1.6:1 and absorbs lone low-contrast cells. Even so, a
  conversion is used only if it is in `icons_apps.CONVERT_OK`, a list of ones
  looked at and approved; everything else gets a letter tile. No measure told
  a recognisable conversion from a shapeless blob (Steam passed every check),
  so look before adding to that list. KIconLoader tries a name's shorter forms, and
  for application-/audio-/image-/inode-/text-/video- names the kind's
  `-x-generic`, in this theme before Breeze Dark, so a name added here can
  hide Breeze icons (Quit became a blank page once);
  `protect_breeze` ships those, and
  `kiconfinder6` with a fake `XDG_CONFIG_HOME`/`XDG_DATA_DIRS` shows what a
  name resolves to. Never draw toolbar actions (`breeze_actions`). The tray
  is the exception: its icons are one-colour glyphs in `icons_tray.py` (an
  11-cell grid, painted with the `ColorScheme-*` classes so Plasma recolours
  them), written first, into `status/`, under plain and `-symbolic` names,
  including the few Breeze files under actions (notifications, brightness,
  `im-user`, the colour picker widget's `color-picker`). Never make tray
  icons coloured sprites or conversions: the battery levels came out as mush
  that way. The build also converts this machine's installed apps' icons into `theme/`: the user
  wants everything Retrograde in the repository, not only in `~/.local/share`.
- The font is Departure Mono (`src/fonts`, OFL, shipped unchanged), set in
  `build_fonts.py`: 12 pt, Konsole too, and 10 pt for the smallest text. A
  pixel font is sharp only where a font pixel is a whole number of screen
  pixels (em 11 px; at 115%, 14.35 pt is 22 px), but the user found 14.35 pt
  too big and chose 12 pt, softer. `font-size.sh` reads a machine's scale
  and uses a sharp size within 1.5 pt of 12 (13.03 pt on the user's 190%
  laptop), else 12. It has no bold, so nothing is set bold.
  Plasma 6.7 applies a global theme's fonts only if its defaults have
  `activeFont` under `[kdeglobals][General]` (its check looks in the wrong
  groups), so keep that extra key.
- The login screen (`build_sddm.py`) is an SDDM theme for the Qt 6 greeter.
  The user's SDDM runs on X11 unscaled at 3440x1440, so its text is in whole
  ems at 1x and its frames are two pixels a cell. It is system-wide: never
  install it; the user runs `sudo ./install-sddm.sh`. Look at it with
  `sddm-greeter-qt6 --test-mode --theme theme/sddm/Retrograde` on an Xvfb
  (the power buttons are hidden there: test mode cannot power off). The
  user's sddm.conf sets `InputMethod=qtvirtualkeyboard`; without an
  `InputPanel` of the theme's own, Qt docks a keyboard over half the screen
  whenever a field has focus, so `Keyboard.qml` holds one, shut until the
  card's button opens it.
- The wallpaper keeps the middle and the right edge calm for Conky Orrery
  (centred) and conky-dashboard (right edge), and keeps the sunset low enough
  that the Orrery's bottom readouts stay on dark sky.

## Extras

`extras/conky-orrery-pixel` and `extras/conky-dashboard-pixel` are copies of
the user's conkies (from ~/git/Conky-themes/Conky_Orrery and
~/git/conky-dashboard), changed to draw shapes on a small canvas and text at
full resolution on top. Change the copies, never the originals.

Both write in Departure Mono. Conky draws in screen pixels (the user's
XWayland scales itself, `Scale=1.15`), so its sharp sizes are 11, 22, 33… px:
both round sizes to those, draw the font unhinted and start text on whole
pixels. The Orrery's hoop labels turn, so they stay soft. Conky reloads a Lua
script the moment it changes, so editing these files changes the user's
running conkies at once: work on a scratch copy and copy the finished file
over. A scratch conky renders on a bare Xvfb with no window manager (under
`kwin_x11` the dashboard drew nothing), with `CONKY_DASHBOARD_HEIGHT=1377`
for the user's work area. The dashboard stays shown (`reveal = "always"`):
XWayland sends conky enter and leave events with stale positions, and a hover
panel hid itself and looked as if it had not started. It draws to a
`cairo_xlib_surface_create` surface each frame, because conky's cached
`conky_surface()` went stale under XWayland and the window stayed empty. Both
configs set `output_backend = 'x11'`: conky 1.25 picks Wayland by default in a
Wayland session, where the Xlib call segfaulted (the dashboard now falls back
to `conky_surface()` there) and conky scales the drawing by 1.15, so the pixel
blocks come out uneven. A nested `kwin_wayland --xwayland` on an Xvfb, with a
`kwinoutputconfig.json` at scale 1.15, tests the Wayland side. conky 1.25
also gives an undecorated window an empty input area, which made the panel
click-through; the dashboard runs `clickable.py` once at start to reset it.
Clicks from XTest on the Xvfb under a nested KWin travel the whole way through
KWin and XWayland, so that is where to test them. To
see what the live panel shows, capture its window read-only with `import
-window <id>` on `DISPLAY=:1` (its `XAUTHORITY` is in `/proc/<pid>/environ`).

The dashboard copy holds **no API key**: it falls back to the original's
`.owm_key`. Never copy or symlink the key into this folder. When testing the
dashboard, render a scratch copy with `refresh_updates`/`refresh_weather` set
to 0, or the first frame fetches weather and runs the update checks.
