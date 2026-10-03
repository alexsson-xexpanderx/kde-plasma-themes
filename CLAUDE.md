# kde-plasma-themes — notes for working in this repository

Each theme lives in its own folder (`Retrograde/`, …) with its own README, its
own `CLAUDE.md` and everything it is built from. Paths in a theme's notes are
relative to its folder. Read that theme's `CLAUDE.md` before working on it.

The user runs their own Plasma session and conkies. Never apply a theme to it,
never restart plasmashell or kwin, and never `pkill conky`; the theme's notes
say how to test in a throwaway session instead.

`extras` at the top level, if it is there, is a local symlink to
`Retrograde/extras`, left when the theme moved into its folder so that the
conkies already running from the old path keep finding their files. It is in
`.git/info/exclude`, not in the repository. Delete it once the conkies have
been started again from `Retrograde/extras` (the autostart entries point
there).
