--[[
    conky-dashboard -- a hover-revealed system panel for Slackware.

    Everything on screen is drawn with cairo; conky.text is empty on purpose.
    Data collection is pure Lua reading /proc and /sys, so a frame costs no
    subprocesses.  Pointer handling uses conky's native mouse hook.

    Entry points (referenced from configs/dashboard.conf):
        conky_start_widgets  -- lua_draw_hook_pre
        conky_mouse_event    -- lua_mouse_hook

    This copy is the pixel-art version, made to sit on the Retrograde
    wallpaper.  Every shape -- gauges, arcs, the weather icon and the bar --
    is drawn onto a canvas pixel_size times smaller than the window with
    antialiasing off, then enlarged with hard edges, so one pixel of the
    panel is one pixel of the wallpaper's art.  The writing is drawn at full
    resolution on a layer of its own, on top, so it stays sharp.  Behind it
    all is the Retrograde Plasma panel's own frame, at screen resolution as
    the panel draws it.  Colours follow the Retrograde palette.
]]

require 'cairo'
-- conky >= 1.22 split the Xlib surface helpers into their own module.  It is
-- absent on older builds, where 'cairo' still carries them, so this is soft.
pcall(require, 'cairo_xlib')

--=============================================================================
-- Configuration
--=============================================================================

local config = {
    -- Fonts.  Any family fontconfig can resolve; weights are separate families.
    -- Departure Mono is the Retrograde theme's font and has one weight.
    font        = "Departure Mono",
    font_light  = "Departure Mono",
    -- Departure Mono is a pixel font, drawn 11 pixels to the em, and sharp
    -- only where each of its pixels covers whole screen pixels, so it comes in
    -- two sizes here: one em for anything asked for under font_small_px (the
    -- labels and small print), and otherwise the nearest whole number of ems,
    -- two at least (the readings).  Text starts on a whole pixel.  0 for a
    -- smooth font, which is then set at the sizes asked for.
    font_em       = 11,
    font_small_px = 15.5,
    -- Whether to ask for bold.  Departure Mono has none, and a bold made up by
    -- smearing it reads badly.
    font_bold   = false,

    -- One multiplier over every size passed to text() and measure().  The
    -- vertical spacing that exists to hold text is scaled by the same factor
    -- through fs() below, so the sections grow with the type instead of the
    -- lines closing up on each other.  Sizes elsewhere in this file are the
    -- 1.0 values; this is the only place to change them all at once.
    --
    -- It is the size wanted, not a promise: on a window too short to hold the
    -- sections at this size, draw_panel steps it down (never below 1.0) until
    -- they fit, so the same setting suits a 1395px work area and a 1048px one.
    font_scale  = 1.25,

    -- Palette: the Retrograde theme's.  A lavender white for everything
    -- structural, the theme's pink as the one accent, coral at the hot end of
    -- a ramp, and gold for the daytime sun -- the colour of the sun setting on
    -- the wallpaper.
    base   = "#E7E4F6",     -- text, rings, ticks, tracks
    accent = "#FF5C8A",     -- highlights, gauge fills, anything wanting attention
    warm   = "#FF8266",     -- hot end of the temperature ramp
    sun    = "#FFD685",     -- the daytime sun, and nothing else

    -- Size of one art pixel, in screen pixels.  The Retrograde wallpaper is
    -- painted about 360 art pixels tall whatever the screen, so the match is
    -- your screen's height divided by 360: 4 at 1440, 3 at 1080, 6 at 2160.
    -- 1 turns the pixel look off and draws the panel smooth.
    pixel_size = 4,

    -- Opacity tiers, same four roles as that theme.  Everything structural is
    -- the same white held at a different weight, which is what gives the look
    -- its consistency.
    opacity_track   = 0.15, -- unfilled rings, hairlines, meter tracks
    opacity_surface = 0.06, -- card fills behind the update rows
    opacity_label   = 0.55, -- captions and secondary text
    opacity_text    = 0.85, -- clock and readouts
    opacity_live    = 0.95, -- accent and temperature fills

    -- Gauges stay accent-coloured below this and only then shift towards
    -- `warm`, so an idle machine never reads as a busy one.
    warm_above_pct = 75,

    -- Background: the Retrograde Plasma panel's own, so the dashboard reads as
    -- a sibling of the bottom panel.  The same night fill at the same
    -- translucency, a one-pixel outline that steps round the corners, a
    -- lighter bevel row under the top edge and a hard black shadow down and
    -- to the right.  It is drawn at screen resolution, like the panel, not on
    -- the art-pixel canvas: the panel's outline is one screen pixel.
    --
    -- KWin blurs what is behind the panel; conky cannot ask for that, so at
    -- 0.86 the wallpaper's stars show through faintly as dots.  1.0 matches
    -- the panel when it goes opaque beside a maximised window.
    bg          = "#100E1C",    -- fill: the theme's CRUST
    bg_alpha    = 0.86,         -- the panel's translucent value; 0 = no background
    bg_outline  = "#312D4A",
    bg_bevel    = "#252239",
    bg_shadow   = 0.5,          -- alpha of the black offset shadow, 0 = none
    -- Gap between the background and the window's top, right and left edges:
    -- 8 is the gap a floating Plasma panel keeps, so the dashboard's right
    -- edge lines up with the panel's.
    bg_margin   = 8,
    -- With bg_alpha 0 there is no background at all and an accent stripe down
    -- the left edge marks the panel instead.  That look is only safe because
    -- own_window_hints carries `below`: the sole thing that can show through
    -- is the desktop.

    -- Pixels left clear at the bottom of the window.  A window manager that
    -- honours panel struts already stops the window above a Plasma panel, so
    -- without this the dashboard's button bar ends up flush against it and
    -- the two read as one cluttered strip.  16 leaves the same 8px gap above a
    -- floating Plasma panel as bg_margin leaves at the top and side (the
    -- floating panel rises 8px into the strut it reserves).  Set 0 to go
    -- right to the edge.
    bottom_gap = 16,

    -- Reveal behaviour.
    --   "auto"   panel is visible until the first mouse event proves that
    --            conky is receiving pointer input, then switches to "hover"
    --   "hover"  only visible while the pointer is on the panel
    --   "always" never hides
    -- "always" here: under XWayland conky is sent enter and leave events with
    -- stale pointer positions, so a hover panel hid itself on its own and
    -- looked as if it had never started.  The buttons and rows still work.
    reveal        = "always",
    trigger_width = 14,     -- px from the right screen edge that pops the panel
    fade_steps    = 3,      -- frames taken to fade in/out

    -- Data refresh.  The panel runs the two collector scripts itself, on a
    -- timer, so launching conky is all that is needed -- there is no cron
    -- entry to install.  Set an interval to 0 to switch a collector off and
    -- feed its file some other way.
    refresh_updates = 900,      -- seconds between update checks
    refresh_weather = 900,      -- seconds between weather fetches

    -- Passed to slackware_updates.bash.  Enable only what applies: each one
    -- is a network round trip, and a missing tool reports Unknown.
    update_checks = {
        sbopkg        = true,
        kernel        = false,
        nvidia        = false,
        google_chrome = false,
        skype         = false,
    },

    -- The SlackBuilds tree the sbopkg check compares against.  Empty means
    -- found automatically: the one under sbopkg.conf's REPO_ROOT with the
    -- newest ChangeLog.txt.  Set an absolute path if that picks the wrong one.
    sbo_tree = "",

    -- Weather.  With no key the weather section is hidden entirely, along
    -- with the fetch that feeds it.
    --
    -- Prefer the key file: this file is tracked by git, so a key written here
    -- is one `git push` away from being public.  `.owm_key` is gitignored.
    owm_api_key      = "",
    -- Empty looks for .owm_key in this folder first, then in the original
    -- dashboard's folder, ~/git/conky-dashboard, so the key never has to be
    -- copied in here -- this folder is part of a theme that may be shared.
    owm_api_key_file = "",
    owm_city         = "Cluj-Napoca",
    owm_ccode        = "RO",

    -- Clicking an update row runs its action.  Keys are the names printed by
    -- slackware_updates.bash, so a checker added there can be given a handler
    -- here without touching anything else.  A row with no entry is inert.
    --   cmd      run directly
    --   script   path relative to this repository
    --   terminal open it in a terminal emulator instead of detaching silently
    update_actions = {
        -- The package manager GUI is not part of this copy; it is launched
        -- from the original dashboard's folder, and the row stays inert if it
        -- is not there.
        Slackpkg = { cmd = (os.getenv("HOME") or "") .. "/git/conky-dashboard/slackpkg-gui/slackpkg-gui" },
        Sbopkg   = { script = "sbopkg_update.sh", terminal = true },
    },

    -- Terminal used for `terminal = true` actions; empty picks the first of
    -- konsole, xfce4-terminal, alacritty, xterm, urxvt that is installed.
    terminal = "",

    -- Bottom bar.  Set confirm_power to false for single-click actions.
    confirm_power = true,
    cmd_poweroff  = "/usr/bin/loginctl poweroff",
    cmd_reboot    = "/usr/bin/loginctl reboot",
    cmd_lock      = "/usr/bin/loginctl lock-session",
}

--=============================================================================
-- Pixels
--
-- Shapes are drawn onto a canvas PIXEL times smaller than the window, with
-- antialiasing off, and the canvas is enlarged onto the window with
-- nearest-neighbour filtering, so each of its pixels lands as a hard-edged
-- square the size of the wallpaper's.  Text never goes onto it: text() and
-- measure() draw on `text_layer`, a full-resolution group composited on top.
--
-- With antialiasing off, anything thinner than one art pixel either vanishes
-- or breaks into dots -- a 1px hairline, a 2px stripe.  So while the
-- canvas is being drawn, line widths are held to one art pixel at least and
-- rectangles are snapped to the art-pixel grid, never narrower than a pixel.
-- These two locals shadow the cairo functions for the rest of the file.
--=============================================================================

local PIXEL = math.max(1, math.floor((tonumber(config.pixel_size) or 1) + 0.5))
local THINNEST = 1.05 * PIXEL

local on_canvas = false     -- true while the panel is being drawn onto the canvas
local text_layer = nil      -- where text() and measure() draw while it is

-- On the canvas a line is a whole number of art pixels wide, at least one: a
-- width in between rasterises as a mix of thinner and thicker steps, and the
-- gauge rings came out lumpy.
local smooth_line_width = cairo_set_line_width
local function cairo_set_line_width(cr, width)
    if on_canvas then
        width = math.max(1, math.floor(width / PIXEL + 0.5)) * THINNEST
    end
    smooth_line_width(cr, width)
end

local smooth_rectangle = cairo_rectangle
local function cairo_rectangle(cr, x, y, w, h)
    if on_canvas then
        local x0 = math.floor(x / PIXEL + 0.5) * PIXEL
        local y0 = math.floor(y / PIXEL + 0.5) * PIXEL
        local x1 = math.max(x0 + PIXEL, math.floor((x + w) / PIXEL + 0.5) * PIXEL)
        local y1 = math.max(y0 + PIXEL, math.floor((y + h) / PIXEL + 0.5) * PIXEL)
        x, y, w, h = x0, y0, x1 - x0, y1 - y0
    end
    smooth_rectangle(cr, x, y, w, h)
end

-- Small glyphs that sit in a line of text -- the droplet, the wind arrow, the
-- network arrows, the row dots, the refresh button -- are drawn with the text,
-- sharp.  At three or four art pixels across they would not survive being
-- pixelated; they read as part of the type, and are kept like it.
local function as_type(draw, cr, ...)
    if text_layer then
        local was = on_canvas
        on_canvas = false
        draw(text_layer, ...)
        on_canvas = was
    else
        draw(cr, ...)
    end
end

-- A sprite: rows of '#' and '.', one art pixel each, centred on x, y and
-- snapped to the art-pixel grid, filled with whatever source is set.
local function sprite(cr, rows, x, y)
    local cols = #rows[1]
    local ox = math.floor(x / PIXEL) - math.floor(cols / 2)
    local oy = math.floor(y / PIXEL) - math.floor(#rows / 2)
    cairo_new_path(cr)
    for j, row in ipairs(rows) do
        local i = 1
        while i <= cols do
            if row:sub(i, i) == "#" then
                local k = i
                while k < cols and row:sub(k + 1, k + 1) == "#" do k = k + 1 end
                cairo_rectangle(cr, (ox + i - 1) * PIXEL, (oy + j - 1) * PIXEL,
                                (k - i + 1) * PIXEL, PIXEL)
                i = k + 1
            else
                i = i + 1
            end
        end
    end
    cairo_fill(cr)
end

--=============================================================================
-- Where we live
--=============================================================================

-- conky resolves lua_load against the *config file's* directory and hands us
-- an absolute path, so the repository runs in place with no install step.
local function script_dir()
    return debug.getinfo(1, "S").source:match("^@(.*)/[^/]*$")
end

-- The state files sit at the repository root, one level above lua/.  Rather
-- than assuming that layout, look for them: this keeps working if the script
-- is moved next to its data, and still falls back to the documented path.
local function locate_base()
    local dir = script_dir()
    if dir then
        for _, candidate in ipairs({ dir .. "/..", dir }) do
            local probe = io.open(candidate .. "/.updates.txt", "r")
            if probe then probe:close() return candidate end
        end
        return dir .. "/.."
    end
    return os.getenv("HOME") .. "/.conky/conky-dashboard"
end

local BASE = locate_base()

local UPDATES_FILE = BASE .. "/.updates.txt"
local WEATHER_FILE = BASE .. "/.weather.txt"

--=============================================================================
-- Small helpers
--=============================================================================

local function hex2rgb(hex)
    -- Falling back to the palette rather than some other grey: a nil colour is
    -- a bug, and it should not quietly introduce a fourth colour to the theme.
    hex = (hex or config.base):gsub("#", "")
    return tonumber(hex:sub(1, 2), 16) / 255,
           tonumber(hex:sub(3, 4), 16) / 255,
           tonumber(hex:sub(5, 6), 16) / 255
end

-- Drawing code names a role rather than a colour.  Each role is one of the
-- three palette colours held at one of the opacity tiers, so re-theming means
-- editing the config block and nothing else.  A literal "#RRGGBB" still works,
-- which is what the heat ramp returns.
local ROLES

local function build_roles()
    ROLES = {
        text    = { config.base,   config.opacity_text    },
        label   = { config.base,   config.opacity_label   },
        track   = { config.base,   config.opacity_track   },
        surface = { config.base,   config.opacity_surface },
        accent  = { config.accent, config.opacity_live    },
        warm    = { config.warm,   config.opacity_live    },
        -- The daytime sun, and only it: a role of its own so it can be
        -- tuned without dragging the CPU and temperature ramps along with it
        -- -- they mean "hot", this means "daylight".  Here it is the gold of
        -- the wallpaper's sun.
        sun     = { config.sun or config.warm, config.opacity_live },
    }
end

local function resolve_colour(colour)
    if not ROLES then build_roles() end
    local role = ROLES[colour]
    if role then return role[1], role[2] end
    return colour, 1
end

local function set_colour(cr, colour, alpha)
    local hex, weight = resolve_colour(colour)
    local r, g, b = hex2rgb(hex)
    cairo_set_source_rgba(cr, r, g, b, (alpha or 1) * weight)
end

-- Vertical gradient from `colour` down to fully transparent, used to fade an
-- area fill away from its own trace line.
local function set_fade(cr, colour, y_solid, y_clear, alpha)
    local hex, weight = resolve_colour(colour)
    local r, g, b = hex2rgb(hex)
    local pattern = cairo_pattern_create_linear(0, y_solid, 0, y_clear)
    cairo_pattern_add_color_stop_rgba(pattern, 0, r, g, b, (alpha or 1) * weight * 0.55)
    cairo_pattern_add_color_stop_rgba(pattern, 1, r, g, b, 0)
    cairo_set_source(cr, pattern)
    cairo_pattern_destroy(pattern)
end

-- Linear blend between two "#RRGGBB" strings, returned in the same form.
local function blend(from, to, t)
    if t < 0 then t = 0 elseif t > 1 then t = 1 end
    local r1, g1, b1 = hex2rgb(from)
    local r2, g2, b2 = hex2rgb(to)
    return string.format("#%02X%02X%02X",
        math.floor((r1 + (r2 - r1) * t) * 255 + 0.5),
        math.floor((g1 + (g2 - g1) * t) * 255 + 0.5),
        math.floor((b1 + (b2 - b1) * t) * 255 + 0.5))
end

local function read_file(path, how)
    local f = io.open(path, "r")
    if not f then return nil end
    local data = f:read(how or "a")
    f:close()
    return data
end

local function read_number(path)
    local v = read_file(path, "l")
    return v and tonumber(v) or nil
end

local function clamp(v, lo, hi)
    if v < lo then return lo elseif v > hi then return hi else return v end
end

-- Rounded rectangle path.
local function rounded_rect(cr, x, y, w, h, r)
    r = math.min(r, w / 2, h / 2)
    cairo_new_sub_path(cr)
    cairo_arc(cr, x + w - r, y + r,     r, -math.pi / 2, 0)
    cairo_arc(cr, x + w - r, y + h - r, r, 0,             math.pi / 2)
    cairo_arc(cr, x + r,     y + h - r, r, math.pi / 2,   math.pi)
    cairo_arc(cr, x + r,     y + r,     r, math.pi,       3 * math.pi / 2)
    cairo_close_path(cr)
end

--=============================================================================
-- Text
--=============================================================================

-- Scale a length that exists to hold text: line spacing, a cap height, a
-- section's own height.  Glyph sizes, gauge radii and clearance around
-- drawings are *not* run through this -- they are not type, and growing them
-- with it is how the weather icon ended up colliding with its caption.
--
-- type_scale is the font_scale in effect: config.font_scale until draw_panel
-- finds the sections do not fit at that size and steps it down.
local type_scale = config.font_scale or 1

local function fs(n)
    return n * type_scale
end

-- The nearest size at which a pixel font's pixels are whole screen pixels.
local function sharp_size(px)
    local em = config.font_em or 0
    if em <= 0 then return px end
    if px < (config.font_small_px or 0) then return em end
    return math.max(2, math.floor(px / em + 0.5)) * em
end

-- A text origin on a whole pixel, for the same reason; left alone for a
-- smooth font.
local function on_pixel(v)
    if (config.font_em or 0) <= 0 then return v end
    return math.floor(v + 0.5)
end

-- A pixel font is drawn unhinted: its outlines already lie on its pixel grid,
-- and hinting only nudges them off it.
local pixel_font_options = nil

local function use_font(cr, family, size, bold)
    cairo_select_font_face(cr, family, CAIRO_FONT_SLANT_NORMAL,
        (bold and config.font_bold) and CAIRO_FONT_WEIGHT_BOLD or CAIRO_FONT_WEIGHT_NORMAL)
    cairo_set_font_size(cr, sharp_size(fs(size)))
    if (config.font_em or 0) > 0 then
        if pixel_font_options == nil then
            pixel_font_options = cairo_font_options_create()
            cairo_font_options_set_hint_style(pixel_font_options, CAIRO_HINT_STYLE_NONE)
            cairo_font_options_set_antialias(pixel_font_options, CAIRO_ANTIALIAS_GRAY)
        end
        cairo_set_font_options(cr, pixel_font_options)
    end
end

local _extents = nil
local function measure(cr, str, family, size, bold)
    cr = text_layer or cr
    use_font(cr, family, size, bold)
    _extents = _extents or cairo_text_extents_t:create()
    cairo_text_extents(cr, str, _extents)
    return _extents.width, _extents.height, _extents.x_bearing, _extents.y_bearing
end

-- The same, by a name the section functions' own `measure` flag cannot hide.
local function text_width(cr, str, family, size, bold)
    return (measure(cr, str, family, size, bold))
end

-- The size to set str at so it is no wider than `width`: the small size for
-- a pixel font, or smaller in proportion for a smooth one.
local function fit_size(cr, str, family, size, bold, width)
    if (config.font_em or 0) > 0 then return config.font_em / type_scale end
    local w = measure(cr, str, family, size, bold)
    return w > width and size * width / w or size
end

-- Draw text with the given horizontal anchor: "left", "center" or "right".
local function text(cr, str, x, y, opts)
    cr = text_layer or cr
    opts = opts or {}
    local family = opts.font or config.font
    local size   = opts.size or 16
    local w      = measure(cr, str, family, size, opts.bold)
    -- opts.fit: the widest it may be.  Wider, it drops to the small size (a
    -- pixel font) or shrinks to fit (a smooth one).
    if opts.fit and w > opts.fit then
        size = fit_size(cr, str, family, size, opts.bold, opts.fit)
        w = measure(cr, str, family, size, opts.bold)
    end
    local align  = opts.align or "left"
    if     align == "center" then x = x - w / 2
    elseif align == "right"  then x = x - w end
    set_colour(cr, opts.colour or "text", opts.alpha or 1)
    cairo_move_to(cr, on_pixel(x), on_pixel(y))
    cairo_show_text(cr, str)
    cairo_new_path(cr)
    return w
end

--=============================================================================
-- Data collection
--
-- Everything here reads /proc, /sys or a plain file.  No process is spawned on
-- the draw path; the one exception is the filesystem gauge, which uses conky's
-- own ${fs_used_perc}, an in-process variable rather than a shell-out.
--=============================================================================

local stats = {
    cpu = 0, mem = 0,
    battery = nil,          -- { percent = n, charging = bool, present = bool }
    weather = {},           -- key/value fields as written by openweather.py
    updates = {},           -- ordered list of { name = "Slackpkg", pending = bool }
    updates_pending = 0,
    net = { name = nil, down = 0, up = 0 },
    uptime = nil,
}

-- ---- Clock ----------------------------------------------------------------
-- os.time() only has one-second resolution, which is too coarse to turn byte
-- counters into rates.  /proc/uptime is monotonic and gives centiseconds.
local function monotonic()
    local line = read_file("/proc/uptime", "l")
    return line and tonumber(line:match("^([%d%.]+)")) or os.time()
end

-- ---- CPU ------------------------------------------------------------------
-- /proc/stat's first line is cumulative jiffies, so a percentage needs the
-- delta against the previous sample.
local prev_total, prev_idle = 0, 0

local function sample_cpu()
    local line = read_file("/proc/stat", "l")
    if not line then return 0 end

    local v = {}
    for n in line:gmatch("%d+") do v[#v + 1] = tonumber(n) end
    if #v < 5 then return 0 end

    local idle, total = v[4] + v[5], 0
    for i = 1, #v do total = total + v[i] end

    local first = (prev_total == 0)
    local dt, di = total - prev_total, idle - prev_idle
    prev_total, prev_idle = total, idle

    -- On the first sample the "delta" is everything since boot, which would
    -- show the lifetime average rather than current load.  Skip that frame.
    if first or dt <= 0 then return 0 end
    return clamp(100 * (dt - di) / dt, 0, 100)
end

-- ---- Memory ---------------------------------------------------------------
local function sample_memory()
    local txt = read_file("/proc/meminfo")
    if not txt then return 0 end
    local total = tonumber(txt:match("MemTotal:%s+(%d+)"))
    -- MemAvailable is what the kernel thinks is actually obtainable; it is a
    -- far better "used" signal than MemFree, which ignores reclaimable cache.
    local avail = tonumber(txt:match("MemAvailable:%s+(%d+)"))
    if not total or not avail or total == 0 then return 0 end
    return clamp(100 * (total - avail) / total, 0, 100)
end

-- ---- Battery --------------------------------------------------------------
-- Lua has no directory listing, so probe the conventional names directly.
local function sample_battery()
    for i = 0, 2 do
        local dir = "/sys/class/power_supply/BAT" .. i
        local pct = read_number(dir .. "/capacity")
        if pct then
            local status = (read_file(dir .. "/status", "l") or ""):lower()
            return {
                present  = true,
                percent  = clamp(pct, 0, 100),
                charging = (status == "charging" or status == "full"),
                full     = (status == "full"),
            }
        end
    end
    return nil          -- desktop: the widget is simply omitted
end

-- ---- Weather --------------------------------------------------------------
-- Written by openweather.py as `key=value` lines.  Keyed rather than
-- positional so the two sides can gain fields independently: anything not
-- recognised here is ignored, anything missing simply is not drawn.
local function sample_weather()
    local txt = read_file(WEATHER_FILE)
    if not txt then return {} end

    local w, keyed = {}, false
    for line in txt:gmatch("[^\n]+") do
        local key, value = line:match("^%s*([%w_]+)%s*=%s*(.-)%s*$")
        if key then
            keyed = true
            w[key] = tonumber(value) or value
        end
    end
    if keyed then return w end

    -- A file left over from the older two-line format: temperature, icon.
    local temp, icon = txt:match("^%s*([%-%d%.]+)%s*\n%s*(%S+)")
    return { temp = tonumber(temp), icon = icon }
end

-- ---- Updates --------------------------------------------------------------
-- Written by slackware_updates.bash as "Name: Updates available".  Parsed
-- generically so adding a checker to the shell script needs no change here.
local function sample_updates()
    local txt = read_file(UPDATES_FILE)
    local list, pending = {}, 0
    if not txt then return list, 0 end
    for line in txt:gmatch("[^\n]+") do
        local name, status = line:match("^%s*([%w%-%+%.]+)%s*:%s*(.-)%s*$")
        if name and status then
            -- Three states, not two: a checker that could not reach the
            -- network reports Unknown, and showing that as "up to date"
            -- would be worse than saying nothing.
            local lowered = status:lower()
            local state = "unknown"
            if lowered:find("^no updates available") then
                state = "ok"
            elseif lowered:find("^updates available") then
                state = "pending"
                pending = pending + 1
            end
            list[#list + 1] = { name = name, state = state, status = status }
        end
    end
    return list, pending
end

-- ---- Network --------------------------------------------------------------
-- Pick the busiest non-loopback interface and turn its byte counters into
-- rates.  Counters are cumulative, so this needs a timed delta.
local prev_net = nil

local function sample_network()
    local txt = read_file("/proc/net/dev")
    if not txt then return stats.net end

    local best_name, best_rx, best_tx = nil, 0, 0
    for line in txt:gmatch("[^\n]+") do
        local iface, rest = line:match("^%s*([%w%-%.@]+):%s*(.+)$")
        if iface and iface ~= "lo" then
            local f = {}
            for n in rest:gmatch("%d+") do f[#f + 1] = tonumber(n) end
            -- field 1 is receive bytes, field 9 is transmit bytes
            if #f >= 9 and (f[1] + f[9]) > (best_rx + best_tx) then
                best_name, best_rx, best_tx = iface, f[1], f[9]
            end
        end
    end
    if not best_name then return { name = nil, down = 0, up = 0 } end

    local now = monotonic()
    -- Carry the cumulative counters too: the graph averages over its own
    -- one-second window rather than reusing this per-frame figure.
    local result = { name = best_name, down = 0, up = 0,
                     rx = best_rx, tx = best_tx, at = now }

    if prev_net and prev_net.name == best_name then
        local dt = now - prev_net.t
        -- Guard against a counter reset (interface down/up) going negative.
        if dt > 0.05 then
            result.down = math.max(0, (best_rx - prev_net.rx) / dt)
            result.up   = math.max(0, (best_tx - prev_net.tx) / dt)
        else
            result.down, result.up = stats.net.down, stats.net.up
        end
    end

    prev_net = { name = best_name, rx = best_rx, tx = best_tx, t = now }
    return result
end

-- ---- Throughput history ---------------------------------------------------
-- Kept at a fixed one-second cadence rather than once per frame, so the graph
-- covers a useful span of time and does not rescale when update_interval does.
local NET_SAMPLES = 96
local net_history = { down = {}, up = {} }
local last_net_sample = 0

local net_mark = nil    -- counters as of the last point plotted

local function record_network(now)
    local net = stats.net
    if not net or not net.rx then return end

    if not net_mark or net_mark.name ~= net.name then
        net_mark = { name = net.name, rx = net.rx, tx = net.tx, t = now }
        return
    end
    if now - last_net_sample < 1 then return end
    last_net_sample = now

    -- Average across the whole second rather than plotting the most recent
    -- frame's rate.  At update_interval = 0.2 that frame covers 200ms, and a
    -- window that short turns ordinary bursts into spikes that dwarf the
    -- actual transfer -- a steady 250 KiB/s download was drawing peaks near
    -- 10 MiB/s before this.
    local span = now - net_mark.t
    local down, up = 0, 0
    if span > 0 then
        down = math.max(0, (net.rx - net_mark.rx) / span)
        up   = math.max(0, (net.tx - net_mark.tx) / span)
    end
    net_mark = { name = net.name, rx = net.rx, tx = net.tx, t = now }

    for key, value in pairs({ down = down, up = up }) do
        local list = net_history[key]
        list[#list + 1] = value
        if #list > NET_SAMPLES then table.remove(list, 1) end
    end
end

-- ---- Uptime ---------------------------------------------------------------
local function sample_uptime()
    local secs = monotonic()
    local d = math.floor(secs / 86400)
    local h = math.floor((secs % 86400) / 3600)
    local m = math.floor((secs % 3600) / 60)
    if d > 0 then return string.format("%dd %dh", d, h) end
    if h > 0 then return string.format("%dh %dm", h, m) end
    return string.format("%dm", m)
end

-- ---- Running the collectors ------------------------------------------------
-- The two collector scripts touch the network and can take seconds, so they
-- are never run on the draw path.  Backgrounding them means os.execute returns
-- as soon as the shell forks, and the child is reparented to init, so there is
-- nothing to block on and no zombie to reap.

local function shell_quote(value)
    return "'" .. (tostring(value):gsub("'", "'\\''")) .. "'"
end

local function spawn_detached(command)
    os.execute(command .. " >/dev/null 2>&1 &")
end

local function readable(path)
    local f = io.open(path, "r")
    if f then f:close() return true end
    return false
end

-- Every one of these takes the command to run after -e, which is the only
-- thing this needs from a terminal.
local TERMINALS = { "konsole", "xfce4-terminal", "alacritty", "xterm", "urxvt" }

-- Checked once: a button whose binary is missing is drawn disabled instead of
-- looking live and then doing nothing.  Only the first word is the program;
-- anything after it is arguments.
local command_cache = {}

local function command_available(command)
    if command_cache[command] == nil then
        local binary = command:match("^%s*(%S+)")
        local ok = false
        if binary then
            if binary:sub(1, 1) == "/" then
                local probe = io.open(binary, "r")
                if probe then probe:close() ok = true end
            else
                -- Bare name: let the shell find it, once, at startup.
                ok = os.execute("command -v " .. binary .. " >/dev/null 2>&1") and true or false
            end
        end
        command_cache[command] = ok
    end
    return command_cache[command]
end

local function terminal_program()
    if config.terminal ~= "" then return config.terminal end
    for _, name in ipairs(TERMINALS) do
        if command_available(name) then return name end
    end
    return nil
end

-- Is there something to run for this row, and can it actually be run?
local function action_for(name)
    local action = (config.update_actions or {})[name]
    if not action then return nil end

    local target = action.cmd
    if action.script then target = BASE .. "/" .. action.script end
    if not target then return nil end

    if action.terminal then
        local term = terminal_program()
        if not term then return nil end
        if not readable(target) then return nil end
        return shell_quote(term) .. " -e " .. shell_quote(target)
    end

    if not command_available(target) then return nil end
    return shell_quote(target)
end


local last_run = { updates = -math.huge, weather = -math.huge }

-- Spawning is separate from the timer so the refresh button can reuse it
-- without having to fake the clock. The script takes its own mkdir lock, so a
-- click landing on top of a scheduled run cannot stack two copies.
local function spawn_update_check()
    if not readable(BASE .. "/slackware_updates.bash") then return false end

    local args = {}
    for name, enabled in pairs(config.update_checks or {}) do
        if enabled then
            args[#args + 1] = "--" .. name:gsub("_", "-")
        end
    end
    if (config.sbo_tree or "") ~= "" then
        args[#args + 1] = "--sbo-tree"
        args[#args + 1] = shell_quote(config.sbo_tree)
    end
    args[#args + 1] = "-o"
    args[#args + 1] = shell_quote(UPDATES_FILE)

    spawn_detached(shell_quote(BASE .. "/slackware_updates.bash") .. " " ..
                   table.concat(args, " "))
    return true
end


local function refresh_updates(now)
    if (config.refresh_updates or 0) <= 0 then return end
    if now - last_run.updates < config.refresh_updates then return end
    if spawn_update_check() then last_run.updates = now end
end

-- The key comes from the config if someone insists, otherwise from a file
-- kept out of version control.
local function owm_key()
    if config.owm_api_key ~= "" then return config.owm_api_key end
    local paths = { config.owm_api_key_file }
    if paths[1] == "" then
        paths = { BASE .. "/.owm_key",
                  (os.getenv("HOME") or "") .. "/git/conky-dashboard/.owm_key" }
    end
    for _, path in ipairs(paths) do
        local raw = read_file(path, "l")
        local key = raw and raw:match("^%s*(%S+)")
        if key then return key end
    end
    return nil
end

local function refresh_weather(now)
    if (config.refresh_weather or 0) <= 0 then return end
    if config.owm_city == "" then return end
    if now - last_run.weather < config.refresh_weather then return end
    if not readable(BASE .. "/openweather.py") then return end

    local key = owm_key()
    if not key then return end
    last_run.weather = now

    -- The key goes in the environment rather than argv so it does not show up
    -- in `ps` against the long-lived python process.
    spawn_detached(string.format(
        "OWM_API_KEY=%s %s --city %s --ccode %s --output %s",
        shell_quote(key),
        shell_quote(BASE .. "/openweather.py"),
        shell_quote(config.owm_city),
        shell_quote(config.owm_ccode),
        shell_quote(WEATHER_FILE)))
end

-- ---- Refresh scheduling ---------------------------------------------------
-- Different readings go stale at wildly different rates, and the cron-written
-- dotfiles only change every five minutes.  Cadences are in seconds so they
-- stay correct no matter what update_interval is set to.
local MEDIUM_EVERY, SLOW_EVERY = 5, 15
local last_medium, last_slow = 0, 0

local function collect()
    local now = monotonic()

    refresh_updates(now)
    refresh_weather(now)

    stats.cpu = sample_cpu()
    stats.mem = sample_memory()
    stats.net = sample_network()
    record_network(now)

    if now - last_medium >= MEDIUM_EVERY then
        last_medium    = now
        stats.battery  = sample_battery()
        stats.uptime   = sample_uptime()
    end

    if now - last_slow >= SLOW_EVERY then
        last_slow      = now
        stats.weather  = sample_weather()
        stats.updates, stats.updates_pending = sample_updates()
    end
end

--=============================================================================
-- Icons
--
-- Drawn as vectors rather than font glyphs.  The original needed Font Awesome
-- Pro, a paid font whose private-use codepoints differ from the Free edition;
-- these cost nothing and scale cleanly.  Each icon is centred on (x, y) and
-- fits a box of roughly `size`.
--=============================================================================

local icons = {}

local function sun(cr, x, y, size, colour, alpha)
    local r = size * 0.28
    set_colour(cr, colour, alpha)
    cairo_arc(cr, x, y, r, 0, 2 * math.pi)
    cairo_fill(cr)

    cairo_set_line_width(cr, math.max(1.4, size * 0.07))
    cairo_set_line_cap(cr, CAIRO_LINE_CAP_ROUND)
    for i = 0, 7 do
        local a = i * math.pi / 4
        local c, s = math.cos(a), math.sin(a)
        cairo_move_to(cr, x + c * r * 1.45, y + s * r * 1.45)
        cairo_line_to(cr, x + c * r * 1.95, y + s * r * 1.95)
    end
    cairo_stroke(cr)
end

local function moon(cr, x, y, size, colour, alpha)
    local r = size * 0.36
    -- The shadow disc has to be bigger than the moon and offset far enough to
    -- cut right through it, or what is left is a ring rather than a crescent.
    -- The remaining sliver is `r - (punch - offset)` thick.
    local punch  = r * 1.40
    local dx, dy = r * 0.53, -r * 0.53

    set_colour(cr, colour, alpha)
    cairo_save(cr)
    -- Clip to the moon first.  An even-odd punch on its own cannot do this: a
    -- shadow that big also pokes outside the disc, and even-odd would fill
    -- that overhang instead of discarding it.
    cairo_arc(cr, x, y, r, 0, 2 * math.pi)
    cairo_clip(cr)
    cairo_set_fill_rule(cr, CAIRO_FILL_RULE_EVEN_ODD)
    cairo_rectangle(cr, x - r * 2, y - r * 2, r * 4, r * 4)
    cairo_new_sub_path(cr)
    cairo_arc(cr, x + dx, y + dy, punch, 0, 2 * math.pi)
    cairo_fill(cr)
    cairo_set_fill_rule(cr, CAIRO_FILL_RULE_WINDING)
    cairo_restore(cr)
end

-- A cloud blob whose bounding width is `size`.
--
-- One path, one fill.  Filling each lobe separately composites the overlaps
-- twice -- at 0.85 opacity two passes land on ~0.98 -- so every seam between
-- the circles shows up as a brighter arc and the cloud looks assembled from
-- parts.  A single fill under the winding rule unions them into one
-- silhouette at a uniform opacity.  All sub-paths must wind the same way for
-- that to hold, which is why every arc runs 0 -> 2pi.
local function cloud(cr, x, y, size, colour, alpha)
    local w = size * 0.9
    set_colour(cr, colour, alpha)

    cairo_new_path(cr)
    cairo_new_sub_path(cr)
    cairo_arc(cr, x - w * 0.22, y,            w * 0.24, 0, 2 * math.pi)
    cairo_new_sub_path(cr)
    cairo_arc(cr, x + w * 0.10, y - w * 0.12, w * 0.30, 0, 2 * math.pi)
    cairo_new_sub_path(cr)
    cairo_arc(cr, x + w * 0.34, y + w * 0.02, w * 0.22, 0, 2 * math.pi)
    rounded_rect(cr, x - w * 0.46, y - w * 0.02, w * 0.92, w * 0.26, w * 0.13)
    cairo_fill(cr)
end

local function rain(cr, x, y, size, colour, alpha, drops)
    set_colour(cr, colour, alpha)
    cairo_set_line_width(cr, math.max(1.5, size * 0.065))
    cairo_set_line_cap(cr, CAIRO_LINE_CAP_ROUND)
    drops = drops or 3
    local spacing = size * 0.22
    local x0 = x - spacing * (drops - 1) / 2
    for i = 0, drops - 1 do
        local dx = x0 + i * spacing
        cairo_move_to(cr, dx + size * 0.05, y)
        cairo_line_to(cr, dx - size * 0.04, y + size * 0.22)
    end
    cairo_stroke(cr)
end

local function bolt(cr, x, y, size, colour, alpha)
    set_colour(cr, colour, alpha)
    local s = size * 0.5
    cairo_move_to(cr, x + s * 0.18, y - s * 0.30)
    cairo_line_to(cr, x - s * 0.22, y + s * 0.12)
    cairo_line_to(cr, x - s * 0.02, y + s * 0.12)
    cairo_line_to(cr, x - s * 0.16, y + s * 0.58)
    cairo_line_to(cr, x + s * 0.26, y + s * 0.02)
    cairo_line_to(cr, x + s * 0.04, y + s * 0.02)
    cairo_close_path(cr)
    cairo_fill(cr)
end

local function snow(cr, x, y, size, colour, alpha)
    set_colour(cr, colour, alpha)
    cairo_set_line_width(cr, math.max(1.2, size * 0.05))
    cairo_set_line_cap(cr, CAIRO_LINE_CAP_ROUND)
    for _, dx in ipairs({ -size * 0.22, 0, size * 0.22 }) do
        local cx, cy, r = x + dx, y + size * 0.12, size * 0.075
        for i = 0, 2 do
            local a = i * math.pi / 3
            cairo_move_to(cr, cx - math.cos(a) * r, cy - math.sin(a) * r)
            cairo_line_to(cr, cx + math.cos(a) * r, cy + math.sin(a) * r)
        end
    end
    cairo_stroke(cr)
end

local function fog(cr, x, y, size, colour, alpha)
    set_colour(cr, colour, alpha)
    cairo_set_line_width(cr, math.max(1.6, size * 0.075))
    cairo_set_line_cap(cr, CAIRO_LINE_CAP_ROUND)
    local widths = { 0.78, 0.92, 0.66, 0.86 }
    for i, fw in ipairs(widths) do
        local ly = y + (i - 2.5) * size * 0.2
        cairo_move_to(cr, x - size * fw / 2, ly)
        cairo_line_to(cr, x + size * fw / 2, ly)
    end
    cairo_stroke(cr)
end

-- OWM icon code -> composed drawing.  Codes are "01".."50" plus d/n suffix.
function icons.weather(cr, code, x, y, size, colour, accent, alpha)
    code = code or ""
    local num   = code:match("^(%d%d)") or "01"
    local night = code:sub(-1) == "n"
    local body  = night and moon or sun
    -- The moon stays on `accent`: it is a pale object and warming it reads as
    -- a harvest moon in every sky. Rain, bolt and snow stay on accent too --
    -- warm precipitation looks like embers.
    local body_colour = night and accent or "sun"

    if num == "01" then
        body(cr, x, y, size, body_colour, alpha)

    elseif num == "02" then
        body(cr, x - size * 0.18, y - size * 0.16, size * 0.78, body_colour, alpha)
        cloud(cr, x + size * 0.10, y + size * 0.14, size * 0.78, colour, alpha)

    elseif num == "03" then
        cloud(cr, x, y, size, colour, alpha)

    elseif num == "04" then
        cloud(cr, x - size * 0.12, y - size * 0.10, size * 0.72, colour, alpha * 0.55)
        cloud(cr, x + size * 0.10, y + size * 0.10, size * 0.86, colour, alpha)

    elseif num == "09" then
        cloud(cr, x, y - size * 0.14, size * 0.92, colour, alpha)
        rain(cr, x, y + size * 0.26, size, accent, alpha, 4)

    elseif num == "10" then
        body(cr, x - size * 0.24, y - size * 0.28, size * 0.62, body_colour, alpha)
        cloud(cr, x + size * 0.06, y - size * 0.06, size * 0.82, colour, alpha)
        rain(cr, x + size * 0.06, y + size * 0.30, size * 0.9, accent, alpha, 3)

    elseif num == "11" then
        cloud(cr, x, y - size * 0.16, size * 0.92, colour, alpha)
        bolt(cr, x, y + size * 0.24, size, accent, alpha)

    elseif num == "13" then
        cloud(cr, x, y - size * 0.16, size * 0.92, colour, alpha)
        snow(cr, x, y + size * 0.22, size, accent, alpha)

    elseif num == "50" then
        fog(cr, x, y, size, colour, alpha)

    else
        cloud(cr, x, y, size, colour, alpha)
    end
end

-- ---- Weather detail glyphs ------------------------------------------------

function icons.refresh(cr, x, y, size, colour, alpha)
    -- A circular arrow needs more room than it looks like it does. The head
    -- must sit at the *end* of the arc pointing along the direction of travel;
    -- putting it at the start aims it into the arc and the whole thing renders
    -- as a ring with a nub, which is what the first attempt did. Checked by
    -- drawing it at real size and magnifying, not by eye at 1x.
    local r = size * 0.34
    set_colour(cr, colour, alpha)
    cairo_set_line_width(cr, math.max(1.0, size * 0.10))
    cairo_set_line_cap(cr, CAIRO_LINE_CAP_ROUND)
    cairo_new_path(cr)
    cairo_arc(cr, x, y, r, -0.60 * math.pi, 1.05 * math.pi)
    cairo_stroke(cr)

    local a      = 1.05 * math.pi
    local px, py = x + math.cos(a) * r, y + math.sin(a) * r
    local tx, ty = -math.sin(a), math.cos(a)     -- tangent: where the arc goes
    local nx, ny =  math.cos(a),  math.sin(a)    -- radial
    local h      = size * 0.44
    cairo_new_path(cr)
    cairo_move_to(cr, px + tx * h * 0.62, py + ty * h * 0.62)
    cairo_line_to(cr, px - tx * h * 0.18 + nx * h * 0.50,
                      py - ty * h * 0.18 + ny * h * 0.50)
    cairo_line_to(cr, px - tx * h * 0.18 - nx * h * 0.50,
                      py - ty * h * 0.18 - ny * h * 0.50)
    cairo_close_path(cr)
    cairo_fill(cr)
end


function icons.droplet(cr, x, y, size, colour, alpha)
    set_colour(cr, colour, alpha)
    local r = size * 0.30
    cairo_new_path(cr)
    cairo_new_sub_path(cr)
    cairo_arc(cr, x, y + size * 0.14, r, 0, 2 * math.pi)
    cairo_new_sub_path(cr)
    cairo_move_to(cr, x - r * 0.80, y + size * 0.06)
    cairo_line_to(cr, x,            y - size * 0.46)
    cairo_line_to(cr, x + r * 0.80, y + size * 0.06)
    cairo_close_path(cr)
    cairo_fill(cr)
end

-- Arrow pointing the way the wind blows.  OWM reports the bearing it comes
-- *from*, hence the half turn.
function icons.wind(cr, x, y, size, degrees, colour, alpha)
    set_colour(cr, colour, alpha)
    cairo_save(cr)
    cairo_translate(cr, x, y)
    cairo_rotate(cr, math.rad((degrees or 0) + 180))
    local h = size * 0.5
    cairo_move_to(cr, 0, -h)
    cairo_line_to(cr, h * 0.60, h * 0.58)
    cairo_line_to(cr, 0, h * 0.22)
    cairo_line_to(cr, -h * 0.60, h * 0.58)
    cairo_close_path(cr)
    cairo_fill(cr)
    cairo_restore(cr)
end

function icons.thermometer(cr, x, y, size, colour, alpha)
    set_colour(cr, colour, alpha)
    local w = size * 0.16
    cairo_new_path(cr)
    rounded_rect(cr, x - w / 2, y - size * 0.44, w, size * 0.62, w / 2)
    cairo_new_sub_path(cr)
    cairo_arc(cr, x, y + size * 0.26, size * 0.20, 0, 2 * math.pi)
    cairo_fill(cr)
end

-- ---- Bottom bar glyphs ----------------------------------------------------

function icons.power(cr, x, y, size, colour, alpha)
    set_colour(cr, colour, alpha)
    cairo_set_line_width(cr, math.max(1.8, size * 0.10))
    cairo_set_line_cap(cr, CAIRO_LINE_CAP_ROUND)
    local r = size * 0.36
    -- ring with a gap at the top, then the stem through the gap
    cairo_arc(cr, x, y, r, -math.pi / 2 + 0.55, -math.pi / 2 - 0.55 + 2 * math.pi)
    cairo_stroke(cr)
    cairo_move_to(cr, x, y - r * 1.05)
    cairo_line_to(cr, x, y - r * 0.12)
    cairo_stroke(cr)
end

function icons.lock(cr, x, y, size, colour, alpha)
    set_colour(cr, colour, alpha)
    local bw, bh = size * 0.62, size * 0.46
    local by = y + size * 0.02
    cairo_set_line_width(cr, math.max(1.8, size * 0.09))
    cairo_set_line_cap(cr, CAIRO_LINE_CAP_ROUND)
    -- shackle
    cairo_arc(cr, x, by - size * 0.02, bw * 0.34, math.pi, 2 * math.pi)
    cairo_stroke(cr)
    -- body
    rounded_rect(cr, x - bw / 2, by, bw, bh, size * 0.09)
    cairo_fill(cr)
end

function icons.reboot(cr, x, y, size, colour, alpha)
    set_colour(cr, colour, alpha)
    cairo_set_line_width(cr, math.max(1.8, size * 0.10))
    cairo_set_line_cap(cr, CAIRO_LINE_CAP_ROUND)
    local r = size * 0.34
    cairo_arc(cr, x, y, r, -math.pi * 0.35, math.pi * 1.25)
    cairo_stroke(cr)
    -- arrowhead at the open end of the arc
    local a  = -math.pi * 0.35
    local hx, hy = x + math.cos(a) * r, y + math.sin(a) * r
    local s  = size * 0.17
    cairo_move_to(cr, hx + s * 0.1, hy - s * 0.95)
    cairo_line_to(cr, hx + s * 0.95, hy + s * 0.15)
    cairo_line_to(cr, hx - s * 0.35, hy + s * 0.35)
    cairo_close_path(cr)
    cairo_fill(cr)
end

-- The bottom bar's icons, redrawn as pixel sprites.  Drawn smooth and then
-- pixelated they came out as unreadable blobs at seven or eight art pixels
-- across; drawn for the grid, nine pixels is plenty for a lock.
local SPRITES = {
    lock = {
        "...###...",
        "..#...#..",
        "..#...#..",
        ".#######.",
        ".###.###.",
        ".###.###.",
        ".#######.",
        ".#######.",
    },
    reboot = {
        "..####.#.",
        ".#....##.",
        "#....###.",
        "#........",
        "#.......#",
        "#.......#",
        ".#.....#.",
        "..#####..",
    },
    power = {
        "....#....",
        ".#..#..#.",
        "#...#...#",
        "#...#...#",
        "#.......#",
        "#.......#",
        ".#.....#.",
        "..#####..",
    },
}

-- The sun riding the daylight arc.
local SUN_SPRITE = {
    "...#...",
    ".#...#.",
    "..###..",
    "#.###.#",
    "..###..",
    ".#...#.",
    "...#...",
}

if PIXEL > 1 then
    for name, rows in pairs(SPRITES) do
        icons[name] = function(cr, x, y, size, colour, alpha)
            set_colour(cr, colour, alpha)
            sprite(cr, rows, x, y)
        end
    end
end

--=============================================================================
-- Widgets
--=============================================================================

-- Colour a reading by how alarming it is: accent up to warm_above_pct, then
-- blended towards `warm`.  Same shape as the calendar theme's heat_color, but
-- keyed to per cent rather than degrees.
local function level_colour(pct)
    local span = 100 - config.warm_above_pct
    if span <= 0 or pct <= config.warm_above_pct then return "accent" end
    return blend(config.accent, config.warm, (pct - config.warm_above_pct) / span)
end

-- A 270-degree ring gauge with the value in the middle and a caption below.
-- Angles run clockwise in cairo's y-down space; the gap sits at the bottom.
local GAUGE_START, GAUGE_SWEEP = 0.75 * math.pi, 1.5 * math.pi

local function ring(cr, x, y, r, pct, caption, alpha, colour)
    local thickness = math.max(3, r * 0.20)
    cairo_set_line_width(cr, thickness)
    cairo_set_line_cap(cr, CAIRO_LINE_CAP_ROUND)

    set_colour(cr, "track", alpha)
    cairo_arc(cr, x, y, r, GAUGE_START, GAUGE_START + GAUGE_SWEEP)
    cairo_stroke(cr)

    if pct > 0.5 then
        set_colour(cr, colour or level_colour(pct), alpha)
        cairo_arc(cr, x, y, r, GAUGE_START, GAUGE_START + GAUGE_SWEEP * pct / 100)
        cairo_stroke(cr)
    end

    text(cr, math.floor(pct + 0.5) .. "%", x, y + fs(r * 0.17),
         { size = r * 0.52, font = config.font_light, align = "center", alpha = alpha })
    text(cr, caption, x, y + r + fs(20),
         { size = 12, colour = "label", align = "center", alpha = alpha })
end

-- Horizontal meter with rounded ends.
local function meter(cr, x, y, w, h, pct, alpha, colour)
    set_colour(cr, "track", alpha)
    rounded_rect(cr, x, y, w, h, h / 2)
    cairo_fill(cr)

    local fill = w * clamp(pct, 0, 100) / 100
    if fill > h then
        set_colour(cr, colour or level_colour(pct), alpha)
        rounded_rect(cr, x, y, fill, h, h / 2)
        cairo_fill(cr)
    end
end

-- Small filled circle used as a status light.
local function dot(cr, x, y, r, colour, alpha)
    set_colour(cr, colour, alpha)
    cairo_arc(cr, x, y, r, 0, 2 * math.pi)
    cairo_fill(cr)
end

--=============================================================================
-- Panel sections
--
-- Each section draws from the cursor `y` and returns the new cursor, so the
-- layout reflows when something is added, removed or resized.
--=============================================================================

--=============================================================================
-- Interaction state
--
-- Declared ahead of the sections because they register their own hit boxes
-- as they draw: the update rows and the bottom bar both write into `ui`.
--=============================================================================

local ui = {
    alpha       = 0,        -- current fade level, 0..1
    revealed    = false,    -- pointer has satisfied the reveal condition
    events_seen = false,    -- conky has delivered at least one mouse event
    pointer     = nil,      -- { x, y } in window coordinates, nil when away
    armed       = nil,      -- id of a power button awaiting confirmation
    armed_at    = 0,
    rows        = {},       -- clickable update rows, rebuilt on every frame
    controls    = {},       -- small in-section buttons, likewise per frame
    checking_at = 0,        -- os.time() of a manual refresh, for the caption
    width       = 0,        -- last known window size, for the mouse hook
    height      = 0,
    buttons     = {},       -- hit boxes rebuilt on every frame
    clickable   = false,    -- clickable.py has been run for this window
}

local ARM_TIMEOUT = 4       -- seconds a confirmation stays armed


local function disarm_if_stale()
    if ui.armed and (os.time() - ui.armed_at) > ARM_TIMEOUT then
        ui.armed = nil
    end
end

local function hit(box, x, y)
    return x >= box.x and x <= box.x + box.w
       and y >= box.y and y <= box.y + box.h
end

local PAD = 26

-- OWM groups the hundreds of weather ids into these nine icon codes; used as
-- a caption when the API's own wording is not in the file.
local CONDITIONS = {
    ["01"] = "Clear", ["02"] = "Few clouds", ["03"] = "Scattered clouds",
    ["04"] = "Overcast", ["09"] = "Showers",  ["10"] = "Rain",
    ["11"] = "Thunderstorm", ["13"] = "Snow", ["50"] = "Mist",
}

local COMPASS = { "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW" }

local function compass(degrees)
    return COMPASS[(math.floor((degrees % 360) / 22.5 + 0.5) % 16) + 1]
end

-- Vertical anchors for the weather block, all relative to its top edge.  Named
-- because the arc has to be placed after the detail row, and getting that
-- wrong silently draws one on top of the other.
local WX_ICON_SIZE             = 148

-- WX_ICON_SIZE is the size the glyph is *drawn to*; the ink it actually puts
-- on the panel is bigger, in both directions, and by different amounts.
-- Measured by rendering every code in isolation and reading the extreme rows
-- off the pixels -- do not re-derive these by reading the drawing code, that
-- is how they were got wrong twice:
--
--     worst above centre  0.642 x size   10d, the sun's rays over a cloud
--     worst below centre  0.574 x size   01d, the bare sun
--
-- which is 180px of ink for a 148px box, 1.22x. Centring the icon on the
-- arithmetic middle of the space leaves it colliding with the caption above
-- and the temperature below, which is exactly what happened.
local WX_ICON_OVER_TOP         = 0.642
local WX_ICON_OVER_BOTTOM      = 0.574
local WX_GAP                   = 14     -- clear space wanted around the glyph
local DAYLIGHT_H               = 74

-- The anchors that hold text move with the type scale, so they are worked out
-- here rather than once at load: draw_panel can step the scale down, and every
-- one of them has to move in step when it does.
local WX_CITY_Y, WX_TEMP_CAP, WX_ICON_Y, WX_TEMP_Y
local WX_DESC_Y, WX_RULE_Y, WX_GLYPH_Y, WX_VALUE_Y, WX_ARC_Y

local function place_weather()
    WX_CITY_Y   = fs(10)
    WX_TEMP_CAP = fs(43)                -- temperature cap height above baseline

    WX_ICON_Y = math.ceil(WX_CITY_Y + 1 + WX_GAP
                          + WX_ICON_SIZE * WX_ICON_OVER_TOP)
    WX_TEMP_Y = math.ceil(WX_ICON_Y + WX_ICON_SIZE * WX_ICON_OVER_BOTTOM
                          + WX_GAP + WX_TEMP_CAP)

    -- Everything below the reading keeps its spacing relative to it, so
    -- changing the icon size moves the whole lower block as one instead of
    -- needing seven numbers edited in step.
    WX_DESC_Y              = WX_TEMP_Y + fs(22)
    WX_RULE_Y              = WX_TEMP_Y + fs(38)
    WX_GLYPH_Y, WX_VALUE_Y = WX_TEMP_Y + fs(56), WX_TEMP_Y + fs(82)
    WX_ARC_Y               = WX_TEMP_Y + fs(98)
end
place_weather()

local function duration(seconds)
    local hours = math.floor(seconds / 3600)
    local mins  = math.floor((seconds % 3600) / 60)
    if hours > 0 then return string.format("%dh %dm", hours, mins) end
    return string.format("%dm", mins)
end

-- The sun's path from sunrise to sunset, with the current position marked.
-- A clock tells you the time; this shows how much daylight is left, which is
-- what you actually look out of the window for.
local function daylight_arc(cr, w, y, alpha)
    local wx = stats.weather
    local sunrise, sunset = wx.sunrise, wx.sunset
    if not sunrise or not sunset or sunset <= sunrise then return 0 end

    -- Wide and shallow: a true semicircle this wide would be 180px tall.
    local rx, ry  = (w - PAD * 2) / 2 - 14, 38
    local cx      = w / 2
    -- Room under the horizon for the sunrise and sunset times.
    local horizon = y + DAYLIGHT_H - 32

    -- Build the path under a squashed CTM but stroke after restoring it,
    -- otherwise the scale distorts the line width along with the shape.
    local function elliptic_path(from, to)
        cairo_save(cr)
        cairo_translate(cr, cx, horizon)
        cairo_scale(cr, 1, ry / rx)
        cairo_new_path(cr)
        cairo_arc(cr, 0, 0, rx, from, to)
        cairo_restore(cr)
    end

    set_colour(cr, "track", alpha)
    cairo_set_line_width(cr, 1.5)
    elliptic_path(math.pi, 2 * math.pi)
    cairo_stroke(cr)

    local progress = (os.time() - sunrise) / (sunset - sunrise)
    local daytime  = progress >= 0 and progress <= 1
    progress = clamp(progress, 0, 1)

    if daytime then
        set_colour(cr, "accent", alpha)
        cairo_set_line_width(cr, 2.5)
        elliptic_path(math.pi, math.pi + math.pi * progress)
        cairo_stroke(cr)
    end

    set_colour(cr, "track", alpha)
    cairo_rectangle(cr, cx - rx - 12, horizon, (rx + 12) * 2, 1)
    cairo_fill(cr)

    local angle  = math.pi + math.pi * progress
    local sx, sy = cx + math.cos(angle) * rx, horizon + math.sin(angle) * ry
    if daytime then
        -- Gold, the colour of the sun setting on the wallpaper.
        if PIXEL > 1 then
            set_colour(cr, "sun", alpha)
            sprite(cr, SUN_SPRITE, sx, sy)
        else
            sun(cr, sx, sy, 16, "sun", alpha)
        end
    else
        -- Below the horizon: mark where it set, or where it will come up.
        dot(cr, sx, sy, 3, "label", alpha * 0.5)
    end

    -- The number you actually want from a daylight arc.
    local now = os.time()
    local remaining
    if daytime then
        remaining = duration(sunset - now) .. " of daylight"
    else
        -- Either side of midnight, the next sunrise is today's or tomorrow's.
        local next_rise = now > sunset and (sunrise + 86400) or sunrise
        remaining = "sunrise in " .. duration(next_rise - now)
    end
    text(cr, remaining, cx, horizon - 9,
         { size = 11, colour = "label", align = "center", alpha = alpha })

    -- Times as observed at the city, not wherever this machine happens to be.
    local tz = wx.tz or 0
    text(cr, os.date("!%H:%M", sunrise + tz), cx - rx - 12, horizon + 28,
         { size = 13, colour = "label", alpha = alpha })
    text(cr, os.date("!%H:%M", sunset + tz), cx + rx + 12, horizon + 28,
         { size = 13, colour = "label", align = "right", alpha = alpha })

    return DAYLIGHT_H
end

-- One reading with a small drawn glyph above it.
local function stat(cr, x, y, glyph, value, alpha, size)
    as_type(glyph, cr, x, y - (WX_VALUE_Y - WX_GLYPH_Y), 15)
    text(cr, value, x, y, { size = size or 12.5, align = "center", alpha = alpha })
end

local function section_weather(cr, w, y, alpha, measure)
    local wx = stats.weather
    if not wx.temp and not wx.icon then return 0 end

    local has_arc = (wx.sunrise and wx.sunset) and DAYLIGHT_H or 0
    local H = has_arc > 0 and (WX_ARC_Y + DAYLIGHT_H) or (WX_VALUE_Y + fs(14))
    if measure then return H end

    local degree = "°"
    local speed  = (wx.units == "imperial") and " mph" or " m/s"
    local middle = w / 2

    -- Place, then the sky itself: the icon leads the panel at full size, with
    -- the reading stacked under it.
    text(cr, (wx.city or config.owm_city or ""):upper(), middle, y + WX_CITY_Y,
         { size = 11.5, colour = "label", align = "center", alpha = alpha })

    icons.weather(cr, wx.icon, middle, y + WX_ICON_Y, WX_ICON_SIZE,
                  "text", "accent", alpha)

    if wx.temp then
        text(cr, string.format("%.0f", wx.temp) .. degree, middle, y + WX_TEMP_Y,
             { size = 58, font = config.font_light, align = "center", alpha = alpha })
    end

    local code = tostring(wx.icon or ""):match("^(%d%d)")
    local caption = wx.description
    if caption then
        caption = caption:sub(1, 1):upper() .. caption:sub(2)
    else
        caption = CONDITIONS[code] or "No weather data"
    end
    -- Feels-like rides along with the condition rather than taking its own
    -- line, which keeps the stack under the icon short.
    if wx.feels and wx.temp and math.abs(wx.feels - wx.temp) >= 1 then
        caption = string.format("%s  ·  feels like %.0f%s", caption, wx.feels, degree)
    end
    text(cr, caption, middle, y + WX_DESC_Y,
         { size = 12.5, colour = "label", align = "center", alpha = alpha,
           fit = w - PAD * 2 })

    set_colour(cr, "track", alpha)
    cairo_rectangle(cr, PAD, y + WX_RULE_Y, w - PAD * 2, 1)
    cairo_fill(cr)

    -- Detail row: only the readings that arrived, spread across the width.
    local cells = {}
    if wx.humidity then
        cells[#cells + 1] = {
            glyph = function(cr2, x, yy, sz) icons.droplet(cr2, x, yy, sz, "accent", alpha) end,
            value = string.format("%d%%", wx.humidity),
        }
    end
    if wx.wind_speed then
        local label = string.format("%.1f%s", wx.wind_speed, speed)
        if wx.wind_deg then label = label .. " " .. compass(wx.wind_deg) end
        cells[#cells + 1] = {
            glyph = function(cr2, x, yy, sz)
                icons.wind(cr2, x, yy, sz, wx.wind_deg, "accent", alpha)
            end,
            value = label,
        }
    end
    if wx.temp_min and wx.temp_max then
        cells[#cells + 1] = {
            glyph = function(cr2, x, yy, sz) icons.thermometer(cr2, x, yy, sz, "accent", alpha) end,
            value = string.format("%.0f%s / %.0f%s", wx.temp_min, degree, wx.temp_max, degree),
        }
    end

    -- One size for the whole row: if any value would crowd its neighbours,
    -- all of them step down together.
    local size, room = 12.5, (w - PAD * 2) / math.max(#cells, 1) - 8
    for _, cell in ipairs(cells) do
        if text_width(cr, cell.value, config.font, size) > room then
            size = fit_size(cr, cell.value, config.font, size, false, room)
        end
    end
    for i, cell in ipairs(cells) do
        stat(cr, PAD + (w - PAD * 2) * (i - 0.5) / #cells, y + WX_VALUE_Y,
             cell.glyph, cell.value, alpha, size)
    end

    if has_arc > 0 then
        daylight_arc(cr, w, y + WX_ARC_Y, alpha)
    end

    return H
end

-- Utilisation only.  Temperature and filesystem use are the calendar widget's
-- job; duplicating them here just made the two conkys argue with each other.
local function section_vitals(cr, w, y, alpha, measure)
    local r = 52
    local H = 2 * r + 6 + fs(40)     -- 6 above the rings, the rest their caption
    if measure then return H end
    local cy = y + r + 6

    ring(cr, w * 0.31, cy, r, stats.cpu, "CPU", alpha)
    ring(cr, w * 0.69, cy, r, stats.mem, "RAM", alpha)

    return H
end

-- Bytes per second in the largest unit that keeps the number small.
local function format_rate(bps)
    if bps >= 1048576 then
        local mib = bps / 1048576
        -- Three significant figures.  Past 100 MiB/s the tenth is noise, and
        -- it is two characters wide on the busiest line in the panel.
        return string.format(mib >= 100 and "%.0f MiB/s" or "%.1f MiB/s", mib)
    end
    if bps >= 1024    then return string.format("%.0f KiB/s", bps / 1024) end
    return string.format("%.0f B/s", bps)
end

-- Small solid triangle; `up` flips it. Drawn rather than typed because the
-- arrow codepoints are missing from plenty of UI fonts.
local function arrow(cr, x, y, size, up, colour, alpha)
    set_colour(cr, colour, alpha)
    local h = size * 0.5
    if up then
        cairo_move_to(cr, x, y - h)
        cairo_line_to(cr, x + h * 0.85, y + h * 0.5)
        cairo_line_to(cr, x - h * 0.85, y + h * 0.5)
    else
        cairo_move_to(cr, x, y + h)
        cairo_line_to(cr, x + h * 0.85, y - h * 0.5)
        cairo_line_to(cr, x - h * 0.85, y - h * 0.5)
    end
    cairo_close_path(cr)
    cairo_fill(cr)
end

local NET_GRAPH_H = 58          -- the plot itself, split either side of the axis
local NET_FLOOR    = 32 * 1024  -- smallest full-scale value, so idle stays flat

-- Trace one series as a path along the top (or bottom) of its half.  Samples
-- are right-aligned, so new readings enter from the right and scroll left.
local function net_trace(cr, series, x, y, w, half, scale, downward)
    local n = #series
    if n < 2 then return false end

    local step = w / (NET_SAMPLES - 1)
    local x0   = x + w - (n - 1) * step
    local base = downward and y or (y + half)

    cairo_new_path(cr)
    for i = 1, n do
        local value = clamp(series[i] / scale, 0, 1)
        local py    = downward and (y + value * half) or (y + half - value * half)
        local px    = x0 + (i - 1) * step
        if i == 1 then cairo_move_to(cr, px, py) else cairo_line_to(cr, px, py) end
    end
    return true, x0, x0 + (n - 1) * step, base
end

local function net_area(cr, series, x, y, w, half, scale, colour, alpha, downward)
    local ok, x0, x1, base = net_trace(cr, series, x, y, w, half, scale, downward)
    if not ok then return end

    -- Fill first: close the trace down to the axis and fade it out towards it.
    cairo_line_to(cr, x1, base)
    cairo_line_to(cr, x0, base)
    cairo_close_path(cr)
    if downward then
        set_fade(cr, colour, y, y + half, alpha)
    else
        set_fade(cr, colour, y + half, y, alpha)
    end
    cairo_fill(cr)

    -- Then the trace itself, at full weight so the shape stays legible when
    -- the fill underneath it is nearly transparent.
    net_trace(cr, series, x, y, w, half, scale, downward)
    set_colour(cr, colour, alpha)
    cairo_set_line_width(cr, 1.6)
    cairo_set_line_join(cr, CAIRO_LINE_JOIN_ROUND)
    cairo_stroke(cr)
end

local function peak_of(series)
    local peak = NET_FLOOR
    for _, value in ipairs(series) do
        if value > peak then peak = value end
    end
    return peak
end

local function section_network(cr, w, y, alpha, measure)
    local net = stats.net
    if not net or not net.name then return 0 end
    -- 124 not 108: the peaks sit on their own line under the readings.  Side
    -- by side they collided on a saturated link -- "934 MiB/s" and its own
    -- peak label do not both fit in half the panel width -- and shrinking the
    -- type to make them fit would hide the one figure that explains why the
    -- two halves of the graph are not to the same scale.
    -- Spelled out rather than left as 124 so the type and the box it has to
    -- fit in cannot drift apart when font_scale moves.
    local H = fs(18) + NET_GRAPH_H + fs(26) + fs(16) + fs(6)
    if measure then return H end

    text(cr, "NETWORK", PAD, y, { size = 11.5, colour = "label", alpha = alpha })
    text(cr, net.name, w - PAD, y,
         { size = 11.5, colour = "label", align = "right", alpha = alpha })

    local gx, gw = PAD, w - PAD * 2
    local gy     = y + fs(18)
    local half   = NET_GRAPH_H / 2
    local axis   = gy + half

    -- Each half is scaled to its own peak.  A shared scale is more honest
    -- about the ratio, but on any ordinary asymmetric link it flattens upload
    -- into the axis and the bottom half stops saying anything; the two peak
    -- figures below carry the magnitude instead.
    local down_peak, up_peak = peak_of(net_history.down), peak_of(net_history.up)

    net_area(cr, net_history.down, gx, gy,   gw, half, down_peak, "accent", alpha, false)
    net_area(cr, net_history.up,   gx, axis, gw, half, up_peak,   "text",   alpha, true)

    set_colour(cr, "track", alpha)
    cairo_rectangle(cr, gx, axis, gw, 1)
    cairo_fill(cr)

    -- Current readings, each with the full-scale value of its own half.  The
    -- peak is labelled rather than left as a bare figure: because the halves
    -- are scaled independently, it is the only thing on screen that says the
    -- two are not drawn to the same scale.  Without the word, an upload peak
    -- of 135 KiB/s drawn as tall as a 5.1 MiB/s download reads as symmetry
    -- rather than as a 39x magnification.
    local row  = gy + NET_GRAPH_H + fs(26)
    local mid  = gx + gw / 2

    as_type(arrow, cr, gx + 6, row - 4, 11, false, "accent", alpha)
    text(cr, format_rate(net.down), gx + 18, row, { size = 13.5, alpha = alpha })
    as_type(arrow, cr, mid + 6, row - 4, 11, true, "text", alpha)
    text(cr, format_rate(net.up), mid + 18, row, { size = 13.5, alpha = alpha })

    -- Each half of the plot is drawn to its own peak, so these two are the
    -- full-scale values -- the only thing on screen saying the halves are not
    -- comparable by height.
    local scale_row = row + fs(16)
    text(cr, "peak " .. format_rate(down_peak), gx + 18, scale_row,
         { size = 9.5, colour = "label", alpha = alpha * 0.8 })
    text(cr, "peak " .. format_rate(up_peak), mid + 18, scale_row,
         { size = 9.5, colour = "label", alpha = alpha * 0.8 })

    return H
end

local function section_battery(cr, w, y, alpha, measure)
    local bat = stats.battery
    if not bat then return 0 end
    local H = fs(10) + 6 + fs(18)    -- header to meter, the meter, the tail
    if measure then return H end

    -- Charging is unremarkable, so it sits at label weight; a draining battery
    -- ramps from accent towards warm as it empties.
    local colour = "accent"
    if bat.charging then
        colour = "label"
    elseif bat.percent <= 30 then
        colour = blend(config.accent, config.warm, (30 - bat.percent) / 30)
    end

    text(cr, bat.charging and "BATTERY — CHARGING" or "BATTERY", PAD, y,
         { size = 11.5, colour = "label", alpha = alpha })
    text(cr, math.floor(bat.percent + 0.5) .. "%", w - PAD, y,
         { size = 12.5, colour = colour, align = "right", alpha = alpha })

    meter(cr, PAD, y + fs(10), w - PAD * 2, 6, bat.percent, alpha, colour)
    return H
end

local UPDATE_ROW_H = 27                 -- at scale 1.0; goes through fs()

local function updates_height()
    if #stats.updates == 0 then return fs(48) end
    return fs(18) + #stats.updates * fs(UPDATE_ROW_H) + fs(6)
end

local function section_updates(cr, w, y, alpha, measure)
    local H = updates_height()
    if measure then return H end
    local pending = stats.updates_pending

    -- Cleared before anything can return early: rows left over from a frame
    -- that had them would otherwise stay clickable over an empty section.
    ui.rows = {}

    text(cr, "UPDATES", PAD, y, { size = 11.5, colour = "label", alpha = alpha })

    -- Manual refresh. The scheduled check is every config.refresh_updates
    -- seconds (15 minutes by default), so after upgrading something by hand
    -- the row can sit there stale for a quarter of an hour stating a fact that
    -- expired moments after it was measured. The hit box is deliberately
    -- larger than the glyph -- 24px for an 13px icon -- because this sits in a
    -- header, not a row, and a 13px target is not one.  The box keeps its size
    -- but its centre follows the header text, which grows upward from its
    -- baseline as the type scale rises.
    ui.controls = {}
    local rb = { x = w - PAD - 18, y = y - fs(2) - 11, w = 24, h = 22, id = "refresh" }
    local rb_hover = ui.pointer and hit(rb, ui.pointer.x, ui.pointer.y) or false
    local checking = (os.time() - ui.checking_at) < 8
    ui.controls[#ui.controls + 1] = rb
    as_type(icons.refresh, cr, rb.x + rb.w / 2, rb.y + rb.h / 2, 15,
                  (rb_hover or checking) and "accent" or "label",
                  alpha * (rb_hover and 1 or 0.85))

    if checking then
        text(cr, "checking…", rb.x - 8, y,
             { size = 11.5, align = "right", alpha = alpha, colour = "accent" })
    elseif #stats.updates > 0 then
        text(cr, pending > 0 and (pending .. " waiting") or "up to date", rb.x - 8, y,
             { size = 11.5, align = "right", alpha = alpha,
               colour = pending > 0 and "accent" or "label" })
    end
    y = y + fs(18)

    if #stats.updates == 0 then
        local note = (config.refresh_updates or 0) > 0
                     and "checking…"
                     or  "update checks are switched off"
        text(cr, note, PAD, y + fs(14),
             { size = 12, colour = "label", alpha = alpha })
        return H
    end

    local row_h = fs(UPDATE_ROW_H)

    for _, item in ipairs(stats.updates) do
        local box = { x = PAD, y = y, w = w - PAD * 2, h = row_h - fs(5) }
        local command = action_for(item.name)
        local hovered = false

        if command then
            box.cmd = command
            ui.rows[#ui.rows + 1] = box
            hovered = ui.pointer and hit(box, ui.pointer.x, ui.pointer.y) or false
        end

        set_colour(cr, hovered and "track" or "surface", alpha * 0.9)
        rounded_rect(cr, box.x, box.y, box.w, box.h, 6)
        cairo_fill(cr)

        local tint  = "label"
        local label = nil
        if item.state == "pending" then
            tint, label = "accent", "update"
        elseif item.state == "unknown" then
            tint, label = "warm", "?"
        end

        local mid = y + box.h / 2
        as_type(dot, cr, PAD + 13, mid, 3.5, tint, alpha)
        text(cr, item.name, PAD + 26, mid + fs(4.5),
             { size = 13, alpha = alpha,
               colour = (item.state == "ok" and not hovered) and "label" or "text" })

        if label then
            text(cr, label, w - PAD - (hovered and 22 or 12), mid + fs(4),
                 { size = 11, colour = tint, align = "right", alpha = alpha })
        end

        -- A chevron on hover is the only hint that a row does anything; rows
        -- with no action in config.update_actions never show one.
        if hovered then
            set_colour(cr, tint, alpha)
            cairo_set_line_width(cr, 1.6)
            cairo_set_line_cap(cr, CAIRO_LINE_CAP_ROUND)
            local cx = w - PAD - 13
            cairo_move_to(cr, cx - 2, mid - 4)
            cairo_line_to(cr, cx + 2, mid)
            cairo_line_to(cr, cx - 2, mid + 4)
            cairo_stroke(cr)
        end

        y = y + row_h
    end
    return H
end

local function section_divider(cr, w, y, alpha, measure)
    local H = 1
    if measure then return H end
    set_colour(cr, "track", alpha)
    cairo_rectangle(cr, PAD, y, w - PAD * 2, 1)
    cairo_fill(cr)
    return H
end

local function section_footer(cr, w, y, alpha, measure)
    if not stats.uptime then return 0 end
    local H = fs(16)
    if measure then return H end

    text(cr, "up " .. stats.uptime, w / 2, y,
         { size = 11.5, colour = "label", align = "center", alpha = alpha })
    return H
end


--=============================================================================
-- Bottom bar
--=============================================================================

local BAR_H = 104

local function section_bar(cr, w, h, alpha)
    local y = h - BAR_H

    set_colour(cr, "surface", alpha * 0.9)
    cairo_rectangle(cr, 2, y, w - 2, BAR_H)
    cairo_fill(cr)

    set_colour(cr, "track", alpha)
    cairo_rectangle(cr, 2, y, w - 2, 1)
    cairo_fill(cr)

    local specs = {
        { id = "lock",     icon = icons.lock,   colour = "text",   cmd = config.cmd_lock,     label = "Lock" },
        { id = "reboot",   icon = icons.reboot, colour = "warm",   cmd = config.cmd_reboot,   label = "Restart" },
        { id = "poweroff", icon = icons.power,  colour = "accent",  cmd = config.cmd_poweroff, label = "Shut down" },
    }

    ui.buttons = {}
    local slot = (w - 4) / #specs
    local cy   = y + BAR_H / 2 - 8

    for i, spec in ipairs(specs) do
        local cx  = 2 + slot * (i - 0.5)
        local box = { x = cx - slot / 2, y = y, w = slot, h = BAR_H,
                      id = spec.id, cmd = spec.cmd }
        ui.buttons[#ui.buttons + 1] = box

        local usable  = command_available(spec.cmd)
        local hovered = usable and ui.pointer and hit(box, ui.pointer.x, ui.pointer.y)
        local armed   = (ui.armed == spec.id)

        box.usable = usable

        if armed or hovered then
            set_colour(cr, armed and spec.colour or "track", alpha * (armed and 0.22 or 0.5))
            rounded_rect(cr, cx - slot / 2 + 8, y + 12, slot - 16, BAR_H - 24, 10)
            cairo_fill(cr)
        end

        local tint = (hovered or armed) and spec.colour or "label"
        spec.icon(cr, cx, cy, 30, tint, alpha * (usable and 1 or 0.35))

        local label = spec.label
        if armed then label = "click again"
        elseif not usable then label = "unavailable" end

        -- A fixed offset from the bottom, not fs(): the type grows upward from
        -- its baseline, so raising the baseline with it as well would walk
        -- the label into the icon.
        text(cr, label, cx, y + BAR_H - 26,
             { size = 10.5, align = "center",
               alpha = alpha * (usable and 1 or 0.5),
               colour = armed and spec.colour or "label" })
    end
end

--=============================================================================
-- Panel
--=============================================================================

-- Gap needed between sections, at scale 1.0, for one header's capitals to
-- clear the section above it.
local MIN_GAP = 12

local function set_type_scale(s)
    type_scale = math.floor(s * 100 + 0.5) / 100
    place_weather()
end

-- The Retrograde panel's frame: each corner row's inset, from the outside row
-- in, and the offset of its hard shadow.  The same numbers the theme's build
-- draws the panel SVG from (frame_grid in src/build_plasma.py).
local FRAME_STEPS  = { 4, 4, 2, 2 }
local FRAME_SHADOW = 4

-- The frame's shape for a box w by h, in whole screen pixels.
local function frame_shape(w, h)
    local f = {}

    function f.cut(row)                         -- a row's inset; nil off the frame
        if row < 0 or row >= h then return nil end
        return FRAME_STEPS[math.min(row, h - 1 - row) + 1] or 0
    end

    -- A row's outline runs in from its own inset to the deeper inset of the
    -- row above or below, so it follows the steps without a gap.  The top
    -- and bottom rows are outline from end to end.
    function f.outline_end(row)
        local c, up, down = f.cut(row), f.cut(row - 1), f.cut(row + 1)
        if not up or not down then return w - c end
        return math.max(c + 1, up, down)
    end

    -- Calls fn(row, count) for each row, except that the rows clear of both
    -- corners, which are all alike, come as one call.
    local plain_top, plain_bottom = #FRAME_STEPS + 1, h - #FRAME_STEPS - 2
    function f.each_row(fn)
        local row = 0
        while row < h do
            if row == plain_top and plain_bottom > plain_top then
                fn(row, plain_bottom - plain_top + 1)
                row = plain_bottom + 1
            else
                fn(row, 1)
                row = row + 1
            end
        end
    end

    return f
end

-- Where the background goes: set in from the window's top and sides by
-- bg_margin, and down to the bottom of the h it is given, since bottom_gap has
-- already taken the room below out of h.  The shadow falls into that room.
-- Nil when there is no background.
local function background_box(w, h)
    if (config.bg_alpha or 0) <= 0 then return nil end
    local m = math.floor(config.bg_margin or 0)
    return m, m, math.floor(w) - 2 * m, math.floor(h) - m
end

local function draw_background(cr, w, h, alpha)
    local x, y, bw, bh = background_box(w, h)
    if not x then return end
    local f = frame_shape(bw, bh)

    local function silhouette(d)
        f.each_row(function(row, count)
            local c = f.cut(row)
            cairo_rectangle(cr, x + d + c, y + d + row, bw - 2 * c, count)
        end)
    end

    cairo_save(cr)
    cairo_set_antialias(cr, CAIRO_ANTIALIAS_NONE)

    -- The shadow is the silhouette moved down and right, less the frame
    -- itself, so none of it darkens what shows through the fill.
    if (config.bg_shadow or 0) > 0 then
        cairo_push_group(cr)
        cairo_set_source_rgb(cr, 0, 0, 0)
        silhouette(FRAME_SHADOW)
        cairo_fill(cr)
        cairo_set_operator(cr, CAIRO_OPERATOR_CLEAR)
        silhouette(0)
        cairo_fill(cr)
        cairo_pop_group_to_source(cr)
        cairo_paint_with_alpha(cr, config.bg_shadow * alpha)
    end

    set_colour(cr, config.bg, config.bg_alpha * alpha)
    silhouette(0)
    cairo_fill(cr)

    if bh > 2 then
        local e = f.outline_end(1)
        set_colour(cr, config.bg_bevel, 0.9 * alpha)
        cairo_rectangle(cr, x + e, y + 1, bw - 2 * e, 1)
        cairo_fill(cr)
    end

    set_colour(cr, config.bg_outline, alpha)
    f.each_row(function(row, count)
        local c, e = f.cut(row), f.outline_end(row)
        if e >= bw - c then
            cairo_rectangle(cr, x + c, y + row, bw - 2 * c, count)
        else
            cairo_rectangle(cr, x + c, y + row, e - c, count)
            cairo_rectangle(cr, x + bw - e, y + row, e - c, count)
        end
    end)
    cairo_fill(cr)
    cairo_restore(cr)
end

-- Clips cr to the inside of the background's outline, so that what the panel
-- draws to the window's edge -- the bottom bar -- stops at the frame rather
-- than running over it.  Does nothing without a background.
local function clip_to_background(cr, w, h)
    local x, y, bw, bh = background_box(w, h)
    if not x then return end
    local f = frame_shape(bw, bh)
    f.each_row(function(row, count)
        local e = f.outline_end(row)
        if bw - 2 * e > 0 then
            cairo_rectangle(cr, x + e, y + row, bw - 2 * e, count)
        end
    end)
    cairo_clip(cr)
end

local function draw_panel(cr, w, h, alpha)
    -- With no background, an accent stripe along the edge marks the panel.
    -- The background itself is drawn by draw_pixelated.
    if (config.bg_alpha or 0) <= 0 then
        set_colour(cr, "accent", alpha * 0.75)
        cairo_rectangle(cr, 0, 0, 2, h)
        cairo_fill(cr)
    end

    -- Two passes: ask every section how tall it is, then share whatever space
    -- is left over equally between them.  The panel therefore fills a 1048px
    -- window and a 1440px one equally well, instead of being tuned to one
    -- screen height with the slack pooling at the bottom.  Sections that have
    -- nothing to show report zero and take no gap.  A divider is not a
    -- section: it is drawn in the middle of the gap before the section it
    -- marks, so it does not give the sections either side of it a gap each and
    -- leave them twice as far apart as the rest.
    local TOP  = 34
    local DIVIDER = "divider"
    local flow = {
        section_weather,
        DIVIDER,
        section_vitals,
        DIVIDER,
        section_network,
        section_battery,
        section_updates,
        section_footer,
    }

    local content, shown, measured
    local function measure_flow()
        content, shown, measured = 0, 0, {}
        for i, section in ipairs(flow) do
            measured[i] = section == DIVIDER and 0 or section(cr, w, 0, alpha, true)
            content = content + measured[i]
            if measured[i] > 0 then shown = shown + 1 end
        end
    end
    measure_flow()

    -- The footer flows with everything else rather than being pinned just
    -- above the bar: pinning it meant a tall panel centred the content and
    -- left an obvious hole between the last card and the footer.
    local bottom = h - BAR_H - 16
    local room   = bottom - TOP - content
    local gaps   = math.max(1, shown - 1)

    -- Too tall at this type scale: step it down until it fits.  A section's
    -- header is drawn with its baseline at the section's top, so its capitals
    -- stand in the gap above; a gap narrower than MIN_GAP lets them touch the
    -- section before.  Only ever downwards, so content that comes and goes
    -- (an update row, the weather) cannot make the type flicker between sizes.
    local min_scale = math.min(1, config.font_scale or 1)
    while room / gaps < fs(MIN_GAP) and type_scale > min_scale + 1e-6 do
        set_type_scale(math.max(min_scale, type_scale - 0.05))
        measure_flow()
        room = bottom - TOP - content
        gaps = math.max(1, shown - 1)
    end

    local gap = clamp(room / gaps, 6, 100)

    -- On a very tall panel the gaps hit their cap before the space is used up.
    -- Centre the whole block rather than letting the remainder pool above the
    -- footer, which is what made a 1440px screen look bottom-heavy.
    local y = TOP + math.max(0, room - gap * gaps) / 2
    local divide = false
    for i, section in ipairs(flow) do
        if section == DIVIDER then
            divide = true
        elseif measured[i] > 0 then
            if divide then section_divider(cr, w, math.floor(y - gap / 2), alpha) end
            divide = false
            section(cr, w, y, alpha)
            y = y + measured[i] + gap
        end
    end

    section_bar(cr, w, h, alpha)
end

-- The whole panel, drawn as pixel art: shapes onto the small canvas, text onto
-- a full-resolution group, then the canvas enlarged onto the window and the
-- text laid over it.
local canvas, canvas_w, canvas_h = nil, 0, 0

local function draw_pixelated(cr, w, h, alpha)
    -- The background is drawn at screen resolution, as the Plasma panel is,
    -- so it goes straight onto the window rather than onto the canvas.
    draw_background(cr, w, h, alpha)

    if PIXEL <= 1 then
        cairo_save(cr)
        clip_to_background(cr, w, h)
        draw_panel(cr, w, h, alpha)
        cairo_restore(cr)
        return
    end

    local cw, ch = math.ceil(w / PIXEL), math.ceil(h / PIXEL)
    if canvas == nil or cw ~= canvas_w or ch ~= canvas_h then
        if canvas then cairo_surface_destroy(canvas) end
        canvas = cairo_image_surface_create(CAIRO_FORMAT_ARGB32, cw, ch)
        canvas_w, canvas_h = cw, ch
    end
    local g = cairo_create(canvas)
    cairo_set_operator(g, CAIRO_OPERATOR_CLEAR)
    cairo_paint(g)
    cairo_set_operator(g, CAIRO_OPERATOR_OVER)
    cairo_scale(g, 1 / PIXEL, 1 / PIXEL)       -- drawn in window coordinates
    cairo_set_antialias(g, CAIRO_ANTIALIAS_NONE)

    cairo_push_group(cr)
    text_layer, on_canvas = cr, true
    local ok, err = pcall(draw_panel, g, w, h, alpha)
    text_layer, on_canvas = nil, false
    local writing = cairo_pop_group(cr)
    cairo_destroy(g)

    cairo_surface_flush(canvas)
    cairo_save(cr)
    clip_to_background(cr, w, h)
    cairo_scale(cr, PIXEL, PIXEL)
    cairo_set_source_surface(cr, canvas, 0, 0)
    cairo_pattern_set_filter(cairo_get_source(cr), CAIRO_FILTER_NEAREST)
    cairo_paint(cr)
    cairo_restore(cr)

    cairo_set_source(cr, writing)
    cairo_paint(cr)
    cairo_pattern_destroy(writing)
    if not ok then error(err, 0) end
end

--=============================================================================
-- Reveal state machine
--=============================================================================

local function target_alpha()
    if config.reveal == "always" then return 1 end
    -- "auto": stay visible until we know pointer input actually reaches us.
    if config.reveal == "auto" and not ui.events_seen then return 1 end
    return ui.revealed and 1 or 0
end

local function step_fade()
    local target = target_alpha()
    local step   = 1 / math.max(1, config.fade_steps)
    if ui.alpha < target then
        ui.alpha = math.min(target, ui.alpha + step)
    elseif ui.alpha > target then
        ui.alpha = math.max(target, ui.alpha - step)
    end
    return ui.alpha
end

--=============================================================================
-- Entry points
--=============================================================================

function conky_start_widgets()
    if conky_window == nil then return end

    -- conky 1.25 gives an undecorated window an empty input area, and the
    -- panel turned click-through.  clickable.py gives the window its input
    -- back; once per start, now that the window exists.  X11 only.
    if not ui.clickable and conky_window.display then
        ui.clickable = true
        spawn_detached("python3 " .. shell_quote(BASE .. "/clickable.py"))
    end

    local w, h = conky_window.width, conky_window.height
    ui.width, ui.height = w, h

    collect()
    disarm_if_stale()

    local alpha = step_fade()
    if alpha <= 0.001 then return end      -- fully hidden: draw nothing at all

    -- Everything lays out from the height it is given, so reserving the gap
    -- here moves the background, the edge stripe and the button bar together.
    local draw_h = math.max(200, h - (config.bottom_gap or 0))

    -- A surface on the window, made each frame.  Not conky_surface(): under
    -- XWayland its cached surface went stale, and the panel drew every frame
    -- without any of it reaching the window, which stayed empty.  Without an
    -- X display (conky on Wayland) the Xlib call would segfault, so that case
    -- takes conky's own surface, which conky keeps and frees itself.
    local surface, own = nil, false
    if conky_window.display and cairo_xlib_surface_create then
        surface, own = cairo_xlib_surface_create(conky_window.display,
            conky_window.drawable, conky_window.visual, w, h), true
    elseif conky_surface then
        surface = conky_surface()
    end
    if surface == nil then return end

    local cr = cairo_create(surface)
    local ok, err = pcall(draw_pixelated, cr, w, draw_h, alpha)
    cairo_destroy(cr)
    if own then cairo_surface_destroy(surface) end

    if not ok then
        io.stderr:write("conky-dashboard: draw failed: " .. tostring(err) .. "\n")
    end
end

-- conky calls this with a table describing the event; see the mouse-events
-- documentation for the fields.  x/y are relative to the conky window.
function conky_mouse_event(event)
    if type(event) ~= "table" then return end

    -- Under XWayland the window gets an enter and a leave the moment it maps,
    -- with the pointer nowhere near it (x = -232).  Taken as input, they
    -- switched "auto" to "hover" and hid the panel before anyone touched it.
    -- Until the pointer has really been over the window, events outside it
    -- prove nothing and are ignored.
    -- The first real event is the pointer on the panel, which is showing:
    -- "auto" turns into "hover" there, still shown, so touching the panel
    -- never makes it vanish.  It hides once the pointer has left it.
    if not ui.events_seen then
        local inside = event.x and event.y and ui.width > 0
                       and event.x >= 0 and event.x < ui.width
                       and event.y >= 0 and event.y < ui.height
        if not inside then return end
        ui.revealed = true
    end
    ui.events_seen = true

    local kind = event.type

    if kind == "mouse_leave" then
        ui.pointer  = nil
        ui.revealed = false
        ui.armed    = nil
        return
    end

    if event.x and event.y then
        ui.pointer = { x = event.x, y = event.y }
    end

    if kind == "mouse_enter" or kind == "mouse_move" then
        -- Pop the panel from a hot edge along the right of the screen, then
        -- keep it up for as long as the pointer stays anywhere on the window.
        if not ui.revealed and ui.width > 0
           and event.x >= ui.width - config.trigger_width then
            ui.revealed = true
        end

    elseif kind == "button_down" and event.button == "left" then
        disarm_if_stale()

        -- Section controls first: they sit in a header, above the rows, and
        -- none of them changes the system -- the refresh only re-runs the
        -- read-only checker.
        for _, box in ipairs(ui.controls) do
            if hit(box, event.x, event.y) then
                ui.armed = nil
                if box.id == "refresh" and spawn_update_check() then
                    ui.checking_at = os.time()
                    last_run.updates = monotonic()
                end
                return
            end
        end

        -- Update rows are plain single-click: nothing here destroys anything,
        -- so they do not need the bottom bar's confirmation step.
        for _, box in ipairs(ui.rows) do
            if hit(box, event.x, event.y) then
                ui.armed = nil
                spawn_detached(box.cmd)
                return
            end
        end

        for _, box in ipairs(ui.buttons) do
            if hit(box, event.x, event.y) and box.usable then
                local needs_confirm = config.confirm_power and box.id ~= "lock"
                if needs_confirm and ui.armed ~= box.id then
                    ui.armed, ui.armed_at = box.id, os.time()
                else
                    ui.armed = nil
                    os.execute(box.cmd .. " >/dev/null 2>&1 &")
                end
                return
            end
        end
        ui.armed = nil      -- clicked somewhere else: cancel a pending action
    end
end

--=============================================================================
-- Development aid
--
-- Render one frame straight to a PNG, with no X server and no conky.  Layout
-- changes can be checked in a second instead of by restarting the desktop:
--
--   lua -e 'package.cpath="/usr/lib64/conky/lib?.so;"..package.cpath
--           dofile("lua/dashboard.lua")
--           conky_dashboard_render("/tmp/panel.png", 400, 1048)'
--=============================================================================

function conky_dashboard_render(path, w, h, alpha, preview)
    w, h = w or 400, h or 1048
    local surface = cairo_image_surface_create(CAIRO_FORMAT_ARGB32, w, h)
    local cr      = cairo_create(surface)

    ui.width, ui.height = w, h
    -- Optional { pointer = {x=,y=}, armed = "poweroff" } to preview the states
    -- that normally need a real pointer.
    if preview then
        ui.pointer = preview.pointer
        ui.armed   = preview.armed
    end
    collect()
    draw_pixelated(cr, w, h, alpha or 1)

    cairo_destroy(cr)
    cairo_surface_write_to_png(surface, path)
    cairo_surface_destroy(surface)
    return path
end
