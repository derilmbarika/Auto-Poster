#!/usr/bin/env python3
"""
Create/update the /sell-rolex/ page on nexchrono.com via WP REST API and set
Rank Math meta (title/description/focus kw) via rankmath/v1/updateMeta.

Reads creds from nexchrono-seo/config.json:
  { "base_url": "https://nexchrono.com", "username": "<wp-login>", "app_password": "xxxx xxxx xxxx ..." }

Idempotent: if a page with slug 'sell-rolex' exists, it updates it; otherwise creates it.
Usage:  python3 push_sell_rolex.py [--dry-run]
"""
import json, os, sys, base64, urllib.request, urllib.error, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(HERE, "config.json")
SLUG = "sell-rolex"
DRY = "--dry-run" in sys.argv

TITLE = "Sell Your Rolex — Get the Best Price, Backed by 25 Years of Expertise"
RM_TITLE = "Sell My Rolex — Free Appraisal & Top Price | NexChrono"
RM_DESC = ("Sell your Rolex to NexChrono: free expert appraisal, same-day offers, secure payment. "
           "25+ years, BBB A+, Myrtle Beach atelier. Get your quote today.")
RM_FOCUS = "sell my rolex"

CONTENT = """<p class="lead">Ready to <strong>sell your Rolex</strong>? NexChrono pays top market price for certified pre-owned Rolex watches — backed by a free expert appraisal, transparent published pricing, and secure same-day payment. Whether you're selling a Submariner, Datejust, Daytona, or any Rolex, our specialists make it simple, safe, and rewarding.</p>

<h2>Why Sell Your Rolex to NexChrono</h2>
<ul>
  <li><strong>Free expert appraisal</strong> — no obligation, no hidden fees. Know exactly what your Rolex is worth.</li>
  <li><strong>Top market price</strong> — we publish fair-market pricing openly and back it with a best-price commitment.</li>
  <li><strong>25+ years of expertise</strong> — established in 1999, BBB A+ rated, with 5-star service.</li>
  <li><strong>Secure, fast payment</strong> — get paid quickly and safely once your watch is verified.</li>
  <li><strong>Sell, trade, or consign</strong> — apply your watch's value toward another piece, or let us sell it for you.</li>
</ul>

<h2>How to Sell Your Rolex in 3 Steps</h2>
<ol>
  <li><strong>Request your free quote.</strong> Tell us your Rolex model, reference number, and condition — include box and papers if you have them.</li>
  <li><strong>Get an expert offer.</strong> Our certified specialists appraise your watch and send you a fair, transparent offer.</li>
  <li><strong>Get paid securely.</strong> Accept the offer, ship insured or visit our Myrtle Beach atelier, and receive fast, secure payment.</li>
</ol>

<h2>Which Rolex Models We Buy</h2>
<p>We purchase all modern and vintage Rolex references in any condition. Popular models we're actively buying include:</p>
<ul>
  <li><a href="/product-category/rolex/submariner/">Rolex Submariner</a> — sell your Submariner, Hulk, Kermit, or no-date</li>
  <li><a href="/product-category/rolex/datejust-41/">Rolex Datejust &amp; Datejust 41</a></li>
  <li><a href="/product-category/rolex/daytona/">Rolex Daytona</a> — including Panda and precious-metal references</li>
  <li><a href="/product-category/rolex/gmt-master-ii/">Rolex GMT-Master II</a> — Pepsi, Batman, Coke</li>
  <li><a href="/product-category/rolex/day-date/">Rolex Day-Date &amp; President</a></li>
  <li>Air-King, Explorer, Sea-Dweller, Sky-Dweller, Oyster Perpetual, Milgauss, Yacht-Master, Cellini</li>
</ul>

<h2>How We Value Your Rolex</h2>
<p>Your offer reflects the model and reference, year of production, overall condition, and whether you have the original box and papers. Because we price against live market data and resell to our own clientele, we can pay more than a typical pawn shop or trade-in counter — and we'll explain every number.</p>

<h2>Sell Your Rolex in Myrtle Beach — or Anywhere in the U.S.</h2>
<p>Visit our atelier at 527 Broadway St, Myrtle Beach, SC 29577 for an in-person appraisal, or sell from anywhere with our fully insured, no-cost shipping. Either way, you deal directly with certified watch experts — never a middleman.</p>

<h2>Frequently Asked Questions</h2>
<h3>How do I sell my Rolex for the best price?</h3>
<p>Request a free appraisal from a specialist who prices against live market data. NexChrono publishes fair-market pricing and backs it with a best-price commitment, so you get top value without the lowball offers common at pawn shops.</p>
<h3>Where can I sell my Rolex for cash near me?</h3>
<p>You can sell your Rolex in person at our Myrtle Beach, SC atelier, or securely from anywhere in the U.S. via insured shipping. Payment is fast and secure once your watch is verified.</p>
<h3>Do I need the box and papers to sell my Rolex?</h3>
<p>No. We buy Rolex watches with or without box and papers. Having the original box, papers, and accessories can increase your offer, but it isn't required.</p>
<h3>How long does it take to get paid?</h3>
<p>After you accept our offer and we verify the watch, payment is issued quickly and securely — typically the same business day for in-person sales.</p>
<h3>Can I trade my Rolex toward another watch?</h3>
<p>Yes. You can apply your Rolex's appraised value toward any watch in our inventory, or consign it and let our specialists sell it for you.</p>

<p class="cta"><a class="button" href="/contact-us/">Get My Free Rolex Appraisal &rarr;</a></p>
"""


def load_cfg():
    if not os.path.exists(CONFIG):
        sys.exit("ERROR: nexchrono-seo/config.json missing. Create it with base_url, username, app_password.")
    with open(CONFIG) as f:
        c = json.load(f)
    c.setdefault("base_url", "https://nexchrono.com")
    if not c.get("username") or not c.get("app_password"):
        sys.exit("ERROR: username / app_password missing in config.json")
    return c


def req(cfg, path, method="GET", body=None, wc=False):
    base = cfg["base_url"].rstrip("/")
    url = base + path
    auth = base64.b64encode(("%s:%s" % (cfg["username"], cfg["app_password"].replace(" ", ""))).encode()).decode()
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header("Authorization", "Basic " + auth)
    r.add_header("Content-Type", "application/json")
    r.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(r, timeout=120) as resp:
            return resp.status, json.loads(resp.read().decode() or "null")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def main():
    cfg = load_cfg()

    # 1. Verify auth + capabilities
    code, me = req(cfg, "/wp-json/wp/v2/users/me?context=edit")
    if code != 200:
        sys.exit("AUTH FAILED (%s): %s" % (code, me))
    print("Authenticated as: %s (id %s)  caps ok" % (me.get("name"), me.get("id")))

    # 2. Find existing page by slug
    code, found = req(cfg, "/wp-json/wp/v2/pages?slug=%s&context=edit" % SLUG)
    page_id = found[0]["id"] if isinstance(found, list) and found else None
    payload = {"title": TITLE, "slug": SLUG, "content": CONTENT, "status": "publish"}

    if DRY:
        print("[dry-run] would %s page slug=%s (existing id=%s)" % ("update" if page_id else "create", SLUG, page_id))
        print("[dry-run] Rank Math: title=%r desc=%r focus=%r" % (RM_TITLE, RM_DESC, RM_FOCUS))
        return

    # 3. Create or update the page
    if page_id:
        code, res = req(cfg, "/wp-json/wp/v2/pages/%s" % page_id, "POST", payload)
    else:
        code, res = req(cfg, "/wp-json/wp/v2/pages", "POST", payload)
    if code not in (200, 201):
        sys.exit("PAGE WRITE FAILED (%s): %s" % (code, res))
    page_id = res["id"]
    print("Page %s -> id %s : %s" % ("updated" if page_id else "created", page_id, res.get("link")))

    # 4. Set Rank Math meta
    rm_body = {
        "objectID": page_id,
        "objectType": "post",
        "meta": {
            "rank_math_title": RM_TITLE,
            "rank_math_description": RM_DESC,
            "rank_math_focus_keyword": RM_FOCUS,
        },
    }
    code, res = req(cfg, "/wp-json/rankmath/v1/updateMeta", "POST", rm_body)
    if code == 200:
        print("Rank Math meta set OK")
    else:
        print("WARN: rankmath/v1/updateMeta returned %s: %s" % (code, res))
        print("Fallback: set the title/description manually in the Rank Math box, or register the meta keys for REST.")

    print("\nDONE. Next: add /sell-rolex/ to nav+footer, inject JSON-LD (see sell-rolex-page.md), purge LiteSpeed cache, submit URL in GSC.")


if __name__ == "__main__":
    main()
