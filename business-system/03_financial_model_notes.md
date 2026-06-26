# Financial Model — Assumptions, Scenarios & Key Outputs
### Companion to `03_financial_model.csv`
**Prepared 2026-06-26 · Currency USD unless noted · FX 1 USD = 1.42 CAD (verify before committing capital)**

> The spreadsheet (`03_financial_model.csv`) is the model. This file documents every assumption, defines the three scenarios, and states the headline outputs (break-even, lowest cash point, profitability timing). **Open the CSV in Google Sheets/Excel to manipulate.** Numbers are modeled from the sourced unit economics in `03_sourcing` research; the **volume ramp is the single biggest assumption** and carries widening uncertainty in later years. Treat Years 2–5 as directional toward the stated Grovemade/Orbitkey-scale goal, not as forecasts.

---

## 1. Unit economics (the foundation — high confidence)
From the sourcing/tariff research (current 2026 regime: de-minimis dead, ~35% China duty stack, Section 122 10% blanket, FX 1.42):

- **Ex-works COGS:** $7.00 · **Landed cost:** $11.49/unit (freight + 35% China duty + inbound). A Vietnam/India second source cuts landed to ~$9.87.
- **Retail:** hero single ~$29; **"Complete Kit" ~$49 (CAD ~$69)**. Blended ASP modeled at **$42** (singles + kits + promo).
- **Gross margin at $49:** 76.6%.
- **Contribution after marketing:** **Walmart-WFS $21.81 (44.5%)**; **Shopify-DTC $11.06 (22.6%)**. Walmart contributes ~2× DTC because WFS ($3.45 all-in) bundles shipping and the 8% referral undercuts DTC's payment + postage stack.
- **Stress test (price −10% AND cost +10%, simultaneously):** both channels stay positive — Walmart +$16.98 (38.5%), DTC +$8.47 (19.2%). **The product is structurally sound.** Breakeven price ≈ $33–35 (DTC) / $24–26 (Walmart) — a $14–23 cushion below the $49 list.

---

## 2. P&L / cash-flow assumptions (Year 1, base)
- **Channel mix:** 60% Walmart / 40% Shopify. Blended contribution-before-marketing **$20.10/unit**; blended variable selling cost **$10.40/unit**.
- **Starting cash:** $40,000 (mid of the $30–50k range). Model also reports the $30k-start case.
- **Founder salary:** $0 in Year 1 (capital preservation). A salary is added from Year 2.
- **Marketing:** ~$21k Year 1 (~8.5% of revenue) — front-loaded into creator seeding (cheap), paid ads only from ~Month 9. This is deliberately content-led because desk-gear paid CAC ($30–70) cannot profitably carry a sub-$50 item early.
- **Fixed opex:** software ramps $40→$120/mo; US 3PL minimum ~$250/mo from Month 4; **one-time ~$4,800 in Month 3** for CPA + customs broker + NRI setup + incorporation.
- **Inventory POs (lumpy cash events):** PO1 800u (~$7.8k, Month 1) → PO2 1,800u US bulk import (~$19.7k incl. duty, Month 4) → PO3 3,500u for Q4 (~$37.2k, Month 8). These lumps, not operating losses, drive the cash low points.
- **Seasonality:** Q4 ramp (Nov/Dec) per category seasonality; January "new desk setup" bump; summer trough. (Demand seasonality detail in Report 01.)

---

## 3. The three scenarios
| | Base | Conservative | Downside |
|---|---|---|---|
| **Story** | Product converts; content gains traction; Walmart search ranks | Slower traction; more paid spend needed | Product fails to differentiate; little organic pull |
| **Year-1 units** | 5,850 | 3,510 (~60%) | 2,050 (~35%) |
| **Year-1 revenue** | $245,700 | $147,420 | $82,000 |
| **Year-1 operating profit** | $88,025 | $33,991 | $4,365 (~breakeven) |
| **Lowest cash (start $40k)** | ~$22k (M4) | ~$9k | ~$6k |
| **Verdict** | Reinvest, scale | Survives, slower | **Kill-criteria territory** — do not reinvest; hold or exit |

**Note on the base operating margin (~36%):** it looks high because the model carries **no salaries, no rent, fully outsourced ops, and content-led (cheap) acquisition.** That is realistic *on paper* for a lean phone-run brand — but it is entirely hostage to the volume assumption. If volume is conservative/downside, the margin compresses fast as paid spend rises. **The risk in this model is the top line, not the unit economics.**

---

## 4. Headline outputs
- **Recommended starting capital:** **CAD $40,000** (≈ USD $28k). Survives base and conservative; $30k survives base only (lowest cash ~$12k at Month 4). The extendable $50k is real insurance for the conservative path.
- **Break-even (contribution basis):** essentially **Month 1** — contribution is positive from the first sales. The meaningful constraint is cash timing around inventory POs, not operating losses.
- **Lowest cash point (base):** **~$22k at Month 4**, caused by the first US bulk-import PO. Never breaches zero with a $40k start.
- **Genuinely phone-run + profitable:** **Month 5–6 (base)** — *after* Phase-0/1 setup is done. Be honest: the build phase (supplier, samples, broker/NRI, listings, first content, or a Kickstarter campaign) is intense laptop work, not light phone work. The business becomes phone-run after it's built.
- **Reinvestment trigger:** 3 consecutive months contribution-positive **and** blended ROAS ≥ 3× → fund the next SKU from cashflow (see Report 07).
- **Kill criteria:** see Report 06 (e.g., samples fail the physical acceptance gate; blended CAC can't get under ~$25; 6 months with no organic traction; Year-1 tracking to downside).

---

## 5. The Kickstarter variant (recommended — improves every cash metric)
The base CSV models a **direct launch** (buy PO1 with cash, then sell), which is the **conservative cash view**. The recommended go-to-market is a **Kickstarter pre-launch** (Report 02/04):
- A campaign **pre-sells PO1**, so the ~$7.8k Month-1 inventory drain is instead **funded by backers**, raising the lowest-cash point from ~$22k toward ~$30k+ and removing the founder's #1 failure mode (over-ordering inventory).
- Realistic first-campaign range for this category is mid-five to high-six figures (Gather ~$430k, Nest ~$646k are top-end; a credible first-timer goal is **$20–80k**, enough to fund PO1 and validate). Kickstarter/payment fees ≈ 8–10% of raised funds; model them as a cost of the pre-sold units.
- A Kickstarter **shifts the calendar** (campaign + manufacturing = ~3–5 months before fulfillment) but **de-risks the capital**, which for a first-timer with a prior inventory wipeout is the right trade. The annual unit economics are unchanged; only timing and cash-risk improve.

**Bottom line:** the unit economics are robust and stress-test-proof; the business is cheap to run and high-margin *if* it hits volume; the capital ask (CAD $40k) is modest and preserved in base/conservative; and a Kickstarter launch removes the largest cash risk. The wager is entirely on demand and differentiation — which is where the risk assessment (Report 06) focuses.
