# Evitania Checklist

[![CI](https://github.com/tamatuk/evitania-checklist/workflows/Check%20PR/badge.svg)](https://github.com/tamatuk/evitania-checklist/actions?query=workflow%3A%22%22Check+PR%22%22)

A progression checklist for **Evitania Online – Idle RPG**: what to have in each
system to reach each stage, a daily task list, and talent builds for your characters.

Open it: <https://tamatuk.github.io/evitania-checklist/>

It is a single self-contained page, `index.html`. No server, no accounts, no
tracking. Your values are kept in your browser and in the page address.

This is a fan project and is not affiliated with the game's developer.

## Put it online with GitHub Pages

1. Create a new **public** repository on GitHub, for example `evitania-checklist`.
2. Push this folder to it:

   ```sh
   cd evitania-checklist
   git init -b main
   git add .
   git commit -m "Evitania Checklist"
   git remote add origin https://github.com/<you>/evitania-checklist.git
   git push -u origin main
   ```

   No git on your machine? Upload only `index.html` and `README.md` through
   **Add file → Upload files**. The page works without `src/`; you only need
   `src/` to rebuild it. (The web uploader takes at most 100 files at a time,
   and `src/icons` holds about 700.)

3. In the repository open **Settings → Pages**, set **Source** to
   _Deploy from a branch_, pick `main` and `/ (root)`, and save.
4. After a minute the page is at `https://<you>.github.io/evitania-checklist/`.

## The Feedback link

The tab bar shows a **Feedback** link when `FEEDBACK_URL` in `src/template.html`
is set. It points to this repository's issues; change it for your fork, for
example to `https://github.com/<you>/evitania-checklist/issues/new`, then
rebuild (below) and push. An empty value hides the link.

## Where your values live

- **Browser storage** (`localStorage`, key `evi-state`): the page remembers you
  on the same browser.
- **The address**: `?share=…` is always in the address and follows every change,
  so the address bar is a link to your current values. Opening a link that
  differs from what the browser has asks before replacing anything.
- **Backup tab**: download, copy or import the same values as JSON.

### Backup JSON (`"v":1`)

```json
{
  "v": 1,
  "stage": "ice-mammoth-dead",
  "tiers": { "hunter": 3, "pusher-gear": 2 },
  "daily": ["quest", "vendor-1"],
  "chars": [["mage", "material-farmer", 63]]
}
```

- `stage`, the `tiers` keys, and the class and role in `chars` are slugs:
  the name in lower case with every run of other characters turned into `-`.
- `stage` is `null` when no stage is picked. Importing `null` clears the stage;
  a backup without `stage`, or with an unknown one, keeps the current stage.
  A renamed stage's old slug imports as the stage it was renamed to.
- `tiers` holds the highest tier reached per system; systems not set are left out.
- `daily` lists the ticked task ids. `chars` rows are `[class, role, level]`.

### Share code

`1` + stage (one base-36 digit, `z` = no stage picked) + one base-36 digit per system (`z` = not set)
\+ `-` + the daily ticks as a base-36 bit mask + `-` + four characters per
character (class index, role index, level as two base-36 digits).

The order of systems and daily tasks in the code is fixed by the `systems` and
`daily` lists in `src/data/share.json`. **Only ever append to those two lists**;
reordering or removing entries breaks links people already have.

## Change the content and rebuild

| File                          | What it holds                                                                    |
| ----------------------------- | -------------------------------------------------------------------------------- |
| `src/data/systems/<sys>.json` | One system each: its name, tiers and rule tables                                 |
| `src/data/stages.json`        | The stages, what reaching each means, and the expected tier per system and stage |
| `src/data/daily.json`         | Daily tasks                                                                      |
| `src/data/roster.json`        | Roster rules for the Talents tab                                                 |
| `src/data/sources.json`       | Every source, by the key the other files cite it with                            |
| `src/data/about.json`         | The About tab's rows                                                             |
| `src/data/share.json`         | The order of systems and daily ids in share codes (append-only)                  |
| `src/data/icons.json`         | Icon groups, name fixes, words that get no icon, aliases and each system's icon  |
| `src/data/trees.json`         | Talent trees: nodes, edges, node kinds' icon files and skill icon order          |
| `src/template.html`           | Page layout, styles and script                                                   |
| `src/build.py`                | Reads `src/data/`, builds the icon sheet and talent trees, writes `index.html`   |
| `src/icons/`                  | Icon images the build packs into the page                                        |

```sh
pip install Pillow
python3 src/build.py
```

That rewrites `index.html` in the repository root. Commit and push it.

To see the page as a pull request proposes it, open the link in the PR's
**PR Preview** comment; each push updates the comment to the latest commit.
The link opens the committed `index.html` on raw.githack, so values saved there
stay apart from the live site's. On a pull request from a fork, the link is in
the job summary of the PR's **PR Preview** check instead.

Things to know when editing `src/data/`:

- **Stages** are numbered 1–10. `reached` in `stages.json` says what reaching
  each stage means; the page shows it beside the stage name and on each stage
  button. `expect` gives each system's expected tier at each stage, one number
  per stage; a stage expects what you need _to reach the next stage_. Its key
  order is the order of systems on the page.
- **Renaming a stage** loses saved progress unless its old name is kept: add
  `"<old name>": "<new name>"` to `aliases` in `stages.json`. The page saves the
  stage by name and backups by slug; share links store the stage number and
  need no alias.
- **A new system** needs a file in `src/data/systems/`, a row in `expect`, an
  icon in `systemIcon` (`icons.json`) and its name appended to `systems` in
  `share.json`.
- **A new daily task** needs a unique `id` on its row in `daily.json`, and the
  same id appended to `daily` in `share.json`.
- **Icons in text** appear when a tier or rule uses the exact in-game name,
  with the same capitals (for example `Enhance Stone 1`, `Thorium Ore`).
- Every tier and rule carries a basis (`Guide`, `Game data`, `Estimate`,
  `Player report`) and its sources: a list of `sources.json` keys, which may be
  empty. A table's `Source` column holds the same kind of list.
- **Source dates** use `date` (YYYY-MM-DD or YYYY-MM) for the source's latest
  publication or update, and optional `read` (YYYY-MM-DD) only when an access
  date was recorded. Earlier dates and sub-notes belong in `name`. When only
  an access date is known, omit `date`; About shows “unknown” rather than
  inventing a publication date. At least one date field is required.
  Freshness uses the publication-date range and latest recorded access date,
  excluding undated sources. Rebuilding unchanged data gives the same page.
  The build rejects malformed dates, impossible calendar dates and legacy
  source-date fields, naming the source key.
- **The build checks the data** and stops naming the file and what is wrong: a
  source key missing from `sources.json`, a `reached` text missing for a stage,
  an alias that is still a stage name or names no stage, an `expect` row without
  one number per stage, a system file with no `expect` row or the reverse, a
  table row with more or fewer cells than its columns, a daily task without a
  unique id, or share lists that do not match the systems and daily ids.
- **Numbers** are written one way. Below 100,000 in full with commas (1,900,
  40,600); from 100,000 up with an uppercase K, M or B (500K, 115.2K, 8.19M).
  The game's Qa and larger suffixes and 1eN exponents stay as the game writes
  them (100Qa, 1e15). A number in a table cell is shown with commas; write one
  of 100,000 or more as text (`"350K"`).
- **Ranges** use an en dash with no spaces, the unit or sign written once:
  25–50%, Tiers 1–3, +4–12, x1.2–1.8. A maxed count is "at N (max)", not "3/3"
  or "42 of 42".
- `mise run lint` checks that the JSON files are formatted; `mise run lint-fix`
  formats them.

## Credits

- Game data and icons come from the community wiki
  [evitania-online.com](https://evitania-online.com/) (repository
  `github.com/badbotexe/evi`, state of 2026-10-11). Skill icons are cropped from
  guide screenshots posted on the game's Discord. All game art belongs to the
  game's developer.
- Guides and data used for each rule are linked next to it on the page.

The code is licensed under [MIT](LICENSE). The licence does not cover the game
art, which belongs to the game's developer.

## Development

### Global dependencies

- [mise](https://mise.jdx.dev/installing-mise.html), activated in the shell (`eval "$(mise activate zsh)"`)

All other tools are pinned in [mise.toml](mise.toml).

### mise tasks

For all commands see [mise.toml](mise.toml) or `mise tasks ls`.
