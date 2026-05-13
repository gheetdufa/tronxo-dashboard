# Tronox 1100 AP Invoice Dashboard

A self-contained, single-file HTML dashboard for analyzing Accounts Payable invoice exceptions. The live version was built around the Tronox Plant 1100 dataset (May 2025 to Jan 2026), but the same file works as a generic template for any AP exception workflow because it can recompute every chart in the browser from CSVs you upload.

Everything that actually ships to the web lives in [`final_dashboard/`](final_dashboard/). Pop open [`final_dashboard/index.html`](final_dashboard/index.html) in any browser and the dashboard runs. No build step, no server, no package install.

## Table of contents

1. [What you get](#what-you-get)
2. [Quick start](#quick-start)
3. [Repo layout](#repo-layout)
4. [Deployment](#deployment)
   - [GitHub Pages via Actions](#github-pages-via-actions)
   - [GitHub Pages via gh-pages branch](#github-pages-via-gh-pages-branch)
   - [Netlify](#netlify)
   - [Vercel](#vercel)
   - [Cloudflare Pages](#cloudflare-pages)
   - [Any static host or local file](#any-static-host-or-local-file)
5. [Tronox-specific notes (handoff)](#tronox-specific-notes-handoff)
6. [Adapting this for your own data](#adapting-this-for-your-own-data)
7. [Modification guide](#modification-guide)
8. [Password gate](#password-gate)
9. [Browser support](#browser-support)
10. [License and credits](#license-and-credits)

---

## What you get

Four tabs of interactive Plotly charts driven entirely by client-side JavaScript:

| Tab | Charts |
|---|---|
| **Overview** | Exception Frequency, Monthly First-Pass Rate, First-Pass Rate by Channel, Exceptions per Invoice |
| **Vendor Analysis** | Vendor exception breakdown (stacked bars), Vendor Processing Complexity bubble chart, click-through Vendor Detail Table with sort and search |
| **Exception Breakdown** | Exceptions by PO Category, Co-occurrence Pairs, Channel x PO Category heatmap, PO category share pie |
| **Trends** | Monthly invoice volume split between first-pass and exception-flagged, with first-pass rate line overlay |

Plus:

- A **KPI strip** with month-over-month deltas for total invoices, first-pass rate, total exception events, and vendor count.
- A **filter toggle** to exclude Exception IDs 0 and 91 and transportation vendors (suppliers whose ID starts with `52`).
- A **password gate** (SHA-256 hashed, client-side only) that hides the UI on load.
- A **Load Your Own Data** modal that recomputes every chart from three CSVs without uploading anything to a server.
- A **lock** button in the header to clear the session and force re-entry of the password.

---

## Quick start

```bash
git clone https://github.com/<your-fork>/tronxo-dashboard.git
cd tronxo-dashboard
open final_dashboard/index.html      # macOS
# or: xdg-open final_dashboard/index.html on Linux
# or: start final_dashboard/index.html on Windows
```

You will see the password gate first. Enter the password the dashboard owner shared with you and the UI unlocks. If you opened the file via `file://`, charts render fine because Plotly and PapaParse load from CDN.

For the custom CSV upload to work over `file://` in some browsers, you may need to serve the folder over HTTP instead:

```bash
python3 -m http.server 8000 --directory final_dashboard
# then visit http://localhost:8000
```

---

## Repo layout

Only the **bolded** items are part of the deployed site. Everything else is historical context kept in the repo for reference and is intentionally not deployed.

```
tronxo-dashboard/
├── final_dashboard/             <-- the only thing that ships
│   ├── index.html               <-- THE dashboard (one file, ~2200 lines)
│   └── .nojekyll                <-- tells GitHub Pages to skip Jekyll
├── .github/workflows/
│   ├── deploy-pages.yml         <-- GitHub Pages via Actions
│   └── sync-gh-pages.yml        <-- mirrors final_dashboard/ to gh-pages branch
├── index.html                   <-- legacy generated dashboard, NOT served
├── output/                      <-- legacy generated artifacts, NOT served
├── analyze.py, analyze_extended.py, build_dashboard*.py  <-- legacy, NOT served
├── data_verify/                 <-- raw invoice universe CSV used for the published numbers
├── 1100 Data inc.csv            <-- raw exception events used for the published numbers
├── 1100 VIM Exceptions Data(DATA - 1100 Sorted) (1).csv
└── .gitignore
```

The published numbers baked into `final_dashboard/index.html` were generated once from the three raw CSVs. After that, the HTML file is the only thing anyone needs to touch.

---

## Deployment

The site is 100% static, so any host that serves files works. The repo ships two ready-to-use GitHub workflows; everything else is a few clicks.

### GitHub Pages via Actions

The fastest path. Recommended.

1. Push the repo to GitHub.
2. Go to **Settings > Pages**.
3. Under **Source**, choose **GitHub Actions**.
4. Push any change to `final_dashboard/` on `main` (or run [`deploy-pages.yml`](.github/workflows/deploy-pages.yml) manually from the **Actions** tab using **Run workflow**).
5. The workflow uploads only the `final_dashboard/` folder. Your site goes live at `https://<user>.github.io/<repo>/`.

The workflow only triggers on changes inside `final_dashboard/**` or to the workflow file itself, so editing `analyze.py` will not redeploy.

### GitHub Pages via gh-pages branch

If you prefer the classic branch-based setup (some orgs enforce this):

1. Go to **Settings > Pages**.
2. Under **Source**, choose **Deploy from a branch**, then pick **gh-pages / (root)**.
3. Push a change to `final_dashboard/` on `main`. The [`sync-gh-pages.yml`](.github/workflows/sync-gh-pages.yml) workflow mirrors `final_dashboard/` to the root of `gh-pages` with `force_orphan: true`, so the branch always contains exactly one file: `index.html` (plus `.nojekyll`).

You can use either workflow, but pick one. Running both is harmless but redundant.

### Netlify

1. Sign in to Netlify and click **Add new site > Import an existing project**.
2. Connect your Git provider and pick the repo.
3. Build settings:
   - **Base directory:** leave blank
   - **Build command:** leave blank
   - **Publish directory:** `final_dashboard`
4. Click **Deploy**. Done.

To wire a custom domain, use Netlify's **Domain management** tab.

### Vercel

1. Sign in to Vercel and click **Add New > Project**.
2. Import the repo.
3. Framework preset: **Other**.
4. **Root directory:** `final_dashboard`.
5. Build and Output Settings: override **Output Directory** to `.` (a single dot) and leave the build command empty.
6. Click **Deploy**.

### Cloudflare Pages

1. From the Cloudflare dashboard, go to **Workers & Pages > Create application > Pages > Connect to Git**.
2. Select the repo.
3. Build settings:
   - **Framework preset:** None
   - **Build command:** leave blank
   - **Build output directory:** `final_dashboard`
4. Click **Save and Deploy**.

### Any static host or local file

The dashboard depends on two CDN scripts (Plotly and PapaParse) loaded over HTTPS, plus the browser's built-in Web Crypto API for SHA-256. There is no server-side code anywhere. So:

- **S3 + CloudFront, Azure Static Web Apps, Firebase Hosting, GitLab Pages, Surge.sh, nginx, Apache:** drop `final_dashboard/index.html` (and `.nojekyll` if your host respects it) at the document root.
- **Local USB or shared drive:** double-click `index.html`. The password gate, charts, KPIs, and tabs all work offline as long as Plotly and PapaParse are reachable from the browser. If you need fully offline use, download `plotly-2.32.0.min.js` and `papaparse.min.js` and rewrite the two `<script src>` URLs in the file to point at local copies.

If the host serves Jekyll by default (GitHub Pages does), keep `final_dashboard/.nojekyll` in place so the file is served untouched.

---

## Tronox-specific notes (handoff)

This section is for whoever takes over the actual Tronox 1100 dashboard. Skip it if you are forking the repo for your own data.

- **Source data window:** May 2025 through Jan 2026, Plant 1100.
- **Three source CSVs** live at the repo root and under `data_verify/`. They are the ground truth for the published numbers:
  - `1100 Data inc.csv` (exception events)
  - `1100 VIM Exceptions Data(DATA - 1100 Sorted) (1).csv` (legacy sorted/filtered exception events)
  - `data_verify/2025 invoices US(1head data) (3).csv` (full posted invoice universe)
- **Vendor exclusions baked into the published numbers:** `SOUTHERN IONICS INCORPORATED` and `TERRA FIRST`. These were dropped from the vendor charts at the request of the audit team. The exclusion is hard-coded in the data baked into `final_dashboard/index.html`; if you rebuild from CSV upload it will not be re-applied automatically.
- **Transportation vendor convention:** any supplier whose ID begins with `52` is treated as transportation. The filter bar toggle hides these.
- **Valid PO types for the "filtered" view:** `NB` and `ZCP`.
- **Strict first-pass methodology (the 13.6% headline KPI):** uses the full posted invoice universe (`Document Status == 15`), and any single exception disqualifies an invoice from first-pass. The "filtered" view (Exc 0 and 91 removed, NB/ZCP only, transport excluded) is the legacy methodology and is what the toggle switches into.
- **Password:** SHA-256 hash sits at line 436 of `final_dashboard/index.html` (`PWD_HASH`). The plaintext is not in the repo. Reach out to the prior owner if you need it.
- **The legacy Python pipeline** (`analyze.py`, `analyze_extended.py`, `build_dashboard*.py`, `output/`) is what originally produced the numbers. It is no longer wired into deployment and the GitHub Actions workflows ignore it on purpose. You can ignore it too unless you want to regenerate from raw CSVs.

---

## Adapting this for your own data

You have two routes.

### Route A: just upload your CSVs (no code changes)

The dashboard ships with an in-browser **Load Your Own Data** button (top right, blue outline). Click it, drop in three CSVs, and every chart and KPI recomputes from your data. Files never leave the browser. Refreshing the page reverts to the published numbers.

Each CSV needs specific columns:

**1. Invoice Universe** (full list of posted invoices, including those with no exceptions)

Required columns:
- `Document Id`
- `Channel ID`
- `PO category decription` (note the typo, kept for backwards-compatibility with the source export)
- `Status Descrip`
- `PO Type descr`
- `Document Create Date`
- `Name 1` (vendor name)

**2. Exception Events (inc)** (every individual exception row)

Required columns:
- `Document Id`
- `Document Status`
- `Supplier`
- `Name 1`
- `PO Type`
- `Channel ID`
- `PO category decription`
- `Exception ID`
- `Exception description`
- `Created at`

**3. Sorted Exceptions** (the same schema as the inc file but pre-filtered to NB/ZCP and excluding Exc 0 and 91; used for the legacy filtered toggle view)

Same columns as file #2.

If your data follows a different schema, rename your columns to match before uploading. It is faster than rewriting the parser.

### Route B: bake new defaults into the file

If you want your data to be the published default (so users do not have to upload anything):

1. Open `final_dashboard/index.html`.
2. Find the `const D = {` line (around line 746). This is the JavaScript object every chart reads from.
3. Replace the values with your own. The shape is documented in inline comments above each key (`monthly`, `exc_freq`, `channel_fp`, `vendor_top30`, etc.).
4. Below that you will find `const E = {` for the extended deep-dive data (exception 91, 151, 29 panels, COUPA + Service explainer).
5. Save and redeploy.

If you want to keep using the legacy Python pipeline to regenerate `D` and `E` from raw CSVs, the scripts are still in the repo. They are not documented here on purpose; treat them as a reference implementation.

---

## Modification guide

Every change below happens in `final_dashboard/index.html`. Search for the marked anchor strings to jump to the right spot.

### Rebrand (logo, title, footer)

| What | Where to look | Default value |
|---|---|---|
| Browser tab title | `<title>` tag near the top | `Tronox 1100 - AP Invoice Dashboard` |
| Header logo text | `<span class="hdr-logo">` | `Tronox` |
| Header subtitle | `<span class="hdr-title">` | `AP Invoice Processing - Plant 1100` |
| Header date meta | `<span class="hdr-meta" id="hdr-meta">` | `Data: May 2025 - Jan 2026` |
| Password gate logo | `<div class="gate-logo">` | `Tronox` |
| Password gate subtitle | `<div class="gate-sub">` | `AP Invoice Dashboard - Restricted Access` |
| Password gate footer | `<div class="gate-foot">` | `Plant 1100 - Confidential` |

### Recolor

Open the `:root { ... }` block near the top of the `<style>` section. The color tokens are:

```css
--blue:   #1a3d6b;   /* primary brand color, header background */
--teal:   #0095a8;   /* secondary accents, KPI highlight */
--green:  #2d9948;   /* "good" KPI color, first-pass success */
--orange: #e8913a;   /* exception highlight */
--red:    #e8503a;   /* alerts, low values in heatmap */
--purple: #7c3aed;   /* extra accent */
--bg, --card, --border, --text, --muted: neutrals
```

Change the hex values and every chart, KPI card, button, and tab indicator will pick up the new palette.

### Add or remove a tab

1. Find `<nav class="tab-nav">` near line 580. Add or remove a `<button class="tab-btn" data-tab="<key>">Label</button>`.
2. Inside `<main class="main">`, add or remove the matching `<div id="tab-<key>" class="tab-pane">` block.
3. If the new tab needs charts, give each chart container a unique `id="ch-..."` and render into it from the script section using Plotly's `newPlot`.
4. The tab switcher (search for `function switchTab`) handles activation automatically off the `data-tab` attribute.

### Vendor exclusions

The two excluded vendors are baked into the pre-aggregated `D.vendor_top30` and `E.e*_vendors` arrays at build time, not filtered at render time. To change them: regenerate the data via Route B above, or simply edit the JSON arrays inside the file to remove rows you do not want.

### First-pass methodology

If you want to redefine what counts as "first-pass" (which exception IDs disqualify, which PO types count, whether to include transport vendors), the cleanest path is to:

1. Compute the new aggregates outside the file (Excel, pandas, SQL, whatever).
2. Paste the new arrays into `D` and `E`.

The in-browser CSV upload path applies a fixed methodology that mirrors the original Python scripts; changing methodology there requires editing the recompute functions inside the file.

---

## Password gate

The dashboard ships locked. The gate is purely client-side and is meant as a soft "do not share publicly" control, not as real authentication. Anyone who downloads the HTML file can read the SHA-256 hash and either reverse it (if the password is weak) or strip the gate entirely.

### Change the password

1. Pick a new password.
2. Compute its SHA-256 hash as lowercase hex. On macOS or Linux:
   ```bash
   printf '%s' 'your-new-password' | shasum -a 256
   ```
   On Windows PowerShell:
   ```powershell
   [BitConverter]::ToString(
     [System.Security.Cryptography.SHA256]::Create().ComputeHash(
       [Text.Encoding]::UTF8.GetBytes('your-new-password')
     )
   ).Replace('-', '').ToLower()
   ```
   Or just open the browser console on the dashboard itself and run `sha256Hex('your-new-password')`. The helper is defined on the page.
3. Open `final_dashboard/index.html`, find `const PWD_HASH = "..."` (around line 436), and replace the hex string with your new hash.
4. Commit and redeploy.

### Remove the gate entirely

Delete the `<div id="gate" class="gate-overlay">` block and the `body class="gate-locked"` attribute. Or simpler: change `body.gate-locked` rules in the CSS so they no longer hide content.

### Reset a session

The hash unlock state is stored in `sessionStorage` under the key `tronox_dash_unlocked`. Clicking the **Lock** button in the header clears it. Closing the tab clears it. Hard-refresh does not clear it (use the lock button).

---

## Browser support

- **Chrome, Edge, Firefox, Safari (current versions):** fully supported.
- **Mobile:** the dashboard has explicit responsive breakpoints. Tabs scroll horizontally on narrow screens.
- **Requirements:** Web Crypto API (`crypto.subtle.digest`, required for the password gate), `sessionStorage`, fetch is not used. Plotly and PapaParse must be reachable from the browser.
- **Strict-CSP or no-CDN environments:** download `plotly-2.32.0.min.js` and `papaparse.min.js` into `final_dashboard/` and rewrite the two `<script src>` lines to point at the local copies. Re-test the **Load Your Own Data** modal after that change.

---

## License and credits

No license file ships with this repo. Add one before publishing your fork. The dashboard uses [Plotly.js](https://plotly.com/javascript/) (MIT) and [PapaParse](https://www.papaparse.com/) (MIT) via CDN.

Original dashboard built for Tronox Plant 1100 AP audit, Jan 2026.
