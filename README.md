# Range Finder — mobile web app

A phone-friendly Butler County off-market land finder. Pulls live county parcel
records, ranks candidates against your criteria, writes outreach letters, and
exports a CSV — from your phone's browser.

## Files

```
index.html                     the whole app — this is all you need to start
netlify/functions/parcels.js   OPTIONAL proxy (only if direct calls are blocked)
netlify.toml                   OPTIONAL config that wires up the proxy
```

The app calls the county GIS directly. Modern ArcGIS servers usually allow that,
so `index.html` alone normally works. If your browser blocks the call (CORS),
add the two optional files and the app automatically routes through the proxy.

---

## Heads up: use the GitHub *website*, not the app

The GitHub mobile **app** can't upload or create files — that only exists on the
website. In your phone browser go to **github.com**, open your `land-finder`
repo, and if the page looks stripped down, open the browser menu and tap
**Request desktop site**, then reload.

## Deploy (from your phone)

1. **Add `index.html` to the repo.**
   On the repo page tap **Add file → Upload files**, pick the `index.html` you
   downloaded from the chat, and **Commit changes**. (Or **Add file → Create new
   file**, name it `index.html`, and paste the contents.)

2. **Publish it on Netlify** (works with a private repo, free).
   - app.netlify.com → sign in with GitHub.
   - **Add new site → Import an existing project →** pick `land-finder`.
   - Build command: leave blank. Publish directory: `.` (a dot). **Deploy.**

3. **Open the `*.netlify.app` URL** on your phone → browser menu → **Add to Home
   Screen.** It now launches like an app.

4. Tap **Find land.** If candidates load, you're done. If it shows a
   "couldn't reach the county server" error, do the one-time fallback below.

### Fallback (only if step 4 errored)
Add `netlify.toml` and `netlify/functions/parcels.js` to the repo (keep that
folder path), commit, and Netlify redeploys. The app starts routing through the
proxy on its own — no other change needed.

> Want to skip Netlify entirely? If you make the repo **public**, you can turn on
> **GitHub Pages** (Settings → Pages → Branch: main) and use that URL instead —
> but Pages can't run the proxy, so only do this if the direct call works.

---

## Using it

- **Search area** — townships load from the county; the zoned ring near 16002 is
  pre-selected, unzoned northern townships are tagged and optional.
- **Find land** — pulls, scores, ranks. Tap a card to expand.
- **Write letter** — pre-fills a letter; your name/phone/email are saved on your
  phone. Copy or Share.
- **Mark contacted** — tracks outreach locally so you don't double-send.

Score (0–100, renormalized) weighs **acreage** (smooth curve, full near 60 ac),
**land share**, **absentee owner**, **zoning tier**, **recorded tenure**, **WMU 2B**
(south of Route 228), **distance to Mars Area High School**, and **budget fit**.
Institutional owners are filtered out; family trusts kept; house parcels included.

**Value & budget.** Each parcel gets an estimated market price: the recorded sale
price if it sold within 7 years, otherwise `acres × the township land rate` plus
`assessed building value × 16.67` (Butler County's 2025-26 Common Level Ratio, since
the county assesses at ~6% of market). Parcels over the **Max budget** field (default
$600k) are hidden. Cards show the estimate broken out (land + building) and combined,
alongside the exact county assessed land / building / total. **The per-township
$/acre rates live in the `PER_ACRE` table at the top of the script — tune them to
your local comps, since they drive both the estimate and the budget filter.**

Each result also has **Google Maps** (drops a pin on the parcel center) and **Search
owner** links, a **Write letter** action (warm, personalized, proper-cased, with a
P.S. referral ask), and a **Print** button that lays out the letter on page 1 and a
fold-for-window-envelope address sheet on page 2. Letter sender details and the
return address are in the `SENDER` constant near the top of the script.

Access, slope, perc, and OGM aren't in county data — each card lists them as a
field-check reminder. Lot lines and value estimates are approximate, and the 2B test
uses an editable Route 228 line (`ROUTE_228`). Prospect with these, don't close on them.

## Tuning
Edit the `CONFIG` block at the top of the `<script>` in `index.html` (weights,
raw-land cutoff, local ZIPs, township sets), commit, and Netlify redeploys. The
command-line `butler_land_finder.py` uses identical scoring for big batch runs.

---

## Cross-device outreach tracking (Supabase)

Each property has an **Outreach** control (Sent / Replied / Interested / Dead) plus
a **notes** field, and a **My outreach** view in the header lists everything you've
tracked. By default this saves on the device. To sync across phone + laptop, point
it at a free Supabase project.

**1. Create the table.** In your Supabase project → SQL Editor, run:

```sql
create table if not exists outreach (
  parcel_id    text primary key,
  status       text,
  notes        text,
  owner        text,
  municipality text,
  acres        numeric,
  updated_at   timestamptz default now()
);
alter table outreach enable row level security;
create policy "anon full access" on outreach
  for all to anon using (true) with check (true);
```

**2. Connect the app.** In Range Finder tap **Sync**, paste your **Project URL**
(Settings → API → Project URL) and **anon / publishable key** (Settings → API),
and Save. The dot turns green when it's syncing. The key is stored only on each
device you enter it on — it is **not** committed to the repo.

**Privacy note:** the policy above lets anyone with your URL + anon key read/write
the table, so treat the tracker as not-secret (it's parcel IDs + your notes). If you
want it locked to just you later, switch to Supabase Auth — ask and we'll wire it up.

---

## Water flags

- **Glade Run** proximity (Glade Run Lake, Middlesex Twp) works immediately — a
  "~X mi Glade Run" flag appears within ~1.5 miles. No data file needed.
- **On-parcel pond / creek** needs a one-time data pull from the USGS National
  Hydrography Dataset, since Butler County's GIS has no water layer:

  ```
  pip install requests
  python fetch_water.py        # writes water.json
  # git add water.json && commit & push
  ```

  Commit `water.json` next to `index.html`. The app loads it and flags parcels a
  stream crosses or a pond sits on, tagging perennial vs. seasonal. Until you add
  the file, on-parcel flags stay dormant (the card shows "add water data"); Glade
  Run still works. Water is a **flag only** right now — it doesn't affect the score.
