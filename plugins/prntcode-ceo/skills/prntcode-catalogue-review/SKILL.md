---
name: prntcode-catalogue-review
description: Monthly catalogue health review for the PRNTCODE Shopify store — audits products against the PRNTCODE Product Tag Standard, checks variant structure (size values, colour casing, missing barcodes, SKU shape), proposes new tags and collections, and rotates the "Lumi's Favs" badge. Reports findings, gets explicit approval, and only then writes to Shopify. Use whenever Khaled says "run the tag review", "catalogue review", "monthly review", "audit the products", "check the tagging", "rotate the badges", "pick Lumi's favourites", asks what state the catalogue is in, or asks whether new collections should exist — also after a new print or drop launches. Prefer this over ad hoc Shopify queries for any question about PRNTCODE product tags, badges, or collections.
---

# PRNTCODE Monthly Catalogue Review

## What this is for

PRNTCODE's catalogue is ~100 products across abayas, ready-to-wear, jalabiyas and accessories, all built from a small set of house prints. Tags are what hold it together: they build the smart collections, they feed storefront search, and — indirectly, via collections — they shape the product recommendations a shopper sees.

Left alone, that structure rots. Colourways get split into new products without colour tags, new drops arrive tagged `Latest` instead of by drop, and badges go stale so the same three products are "Lumi's Favs" for a year.

This review is the maintenance pass. It runs monthly, reports what it found, and **changes nothing without Khaled saying yes.**

Khaled has limited website development experience. Explain anything technical in plain language, and define Shopify jargon briefly the first time it appears.

## The one rule that matters most

**Never write to Shopify before Khaled approves.** Not tags, not badges, not collections. The report comes first, every time.

This is not caution for its own sake. Tags on this store are load-bearing — `measurements` triggers a customer-facing input box, and smart collections rebuild themselves the instant a tag changes. A wrong write is visible to customers within seconds. Proposing first costs one message; fixing a bad bulk write costs an afternoon.

If Khaled doesn't respond, deliver the report and stop. A silent run that changed nothing is a good outcome.

---

## Step 1 — Load the standard

Read the project doc `claude/prntcode-product-tag-standard.md` with the Projects tool (`project_read`).

That document defines 14 facets, each with a closed vocabulary — a fixed list of allowed values. **Do not invent tag values that aren't in it.** If the catalogue clearly needs a value that doesn't exist yet (a new print, a new colour shade), that's a finding to propose in the report, not something to apply silently.

If the doc is missing, stop and tell Khaled — the review has no meaning without it.

## Step 2 — Pull the catalogue

Use the Shopify connector's `graphql_query` tool. See `references/graphql-recipes.md` for the exact queries.

Two things that will waste a run if you get them wrong:

- **Don't use `search_products` for the full catalogue.** Its output exceeds the token limit and gets truncated, and you won't reliably notice.
- **Paginate at 50** using `pageInfo.hasNextPage` and `endCursor` until exhausted. The store has more products than one page.

Skip `ARCHIVED` products. Include `DRAFT` ones but treat them separately — they're often work in progress, not errors.

## Step 3 — Audit tags against the standard

For each product, derive what can be derived and compare it to what's actually there. Roughly 80% needs no judgement — the standard's "machine-derivable" table lists the sources. In brief: fabric and style code from the handle or SKU, silhouette and print from the title, category from `productType`, coverage from silhouette, price tier from price, reversible from the title.

Where colour can't be determined from handle, title or variant options, assign `_qa:no-colour`. **Don't guess a colour.** A wrong colour tag is worse than a missing one because it surfaces the product in the wrong filter and nobody notices.

Sort every difference into three buckets. The buckets exist so Khaled can approve the safe majority in one word without having to read the ambiguous cases at the same time:

- **A — High confidence additions.** Derivable with certainty. No judgement involved.
- **B — Corrections.** Tags that are wrong, misspelled, wrong case, or retired.
- **C — Needs a decision.** Colour gaps, merchandising rotation, occasion, contradictions, and anything listed under "Known data problems" in the standard.

### Tags that must never be auto-changed

`measurements` (lowercase) is wired to site behaviour — it renders a measurement input box so made-to-measure clients can submit their sizes. It is not descriptive metadata. Never rename it, never case-correct it, never remove it in a bulk pass. If a product looks like it has it wrongly, that's a bucket C finding.

## Step 3b — Audit variant structure

Tags describe a product. **Options describe how it varies**, and they rot in a different way — quietly, because nothing on the storefront looks broken.

This matters beyond tidiness: packaging labels are generated from product data, and inconsistent option values produce labels that disagree with the store.

Pull `options { name linkedMetafield { key } optionValues { id name linkedMetafieldValue } }` alongside the catalogue in step 2.

### What the store's convention actually is

Establish this from the data each run rather than assuming — it has already been misread once.

- **A colourway is a separate product, and the colour lives in the SKU**, not in an option. Roughly 20 abayas and every RTW product share a title with a sibling and carry only a Size option. This is the norm, not a defect. **Do not propose adding Colour options across the catalogue** — it is a large customer-visible restructure to serve tooling, and the SKU already carries the fact.
- **Accessories are the exception** and do carry a Colour option, because a scrunchie's colourways sit on one product.
- Jalabiyas vary on `Fabric` and `Fabric or Stitched`, not Size. A different axis, not an error.

### What to actually check

**Size values must be `Small` / `Medium` / `Large`.** Shopify's size taxonomy contains both `Large` and `L` as distinct entries, and a product linked to the wrong one displays `L` while its siblings display `Large`. Three Flutter Dot abayas were linked this way and it was invisible until the values were listed side by side. The fix is to relink `linkedMetafieldValue`, not to rename — an option cannot mix linked and unlinked values, so a plain rename is rejected.

**Colour values must be Title Case and must name a colour only.** Several accessory colours were created as custom metaobjects reading `BLACK`, `BROWN`, `MAROON`, `NAVY`, `SAFFRON`, and one as `Metamorphasis Lavender` — which is misspelled and repeats the print already in the title.

**These are bucket C, never bucket A.** A colour option value is a customer-visible swatch. Correcting it means relinking to a different metaobject, which changes what a shopper sees, and the correct standard entry has to be identified first. Propose it; never apply it in a bulk pass.

**Every variant needs `barcode = SKU`.** The ops app identifies garments by barcode, and Shopify does not set it on product creation — so a barcode is missing on every variant created since the Phase 0 backfill until someone sets it. Report any variant with a null or empty barcode; this is bucket A, since the value is derivable with certainty from the SKU.

**Flag `Default Title`.** A product whose only option is `Title / Default Title` has no real variants. Sometimes correct for a one-size item, sometimes a sign the options were never set up — check against its siblings before deciding.

**Report SKU shape.** The convention is `BRAND-TYPE-PRINT-COLOUR-SIZE`, e.g. `JGLEDT-ABY-BLM-NVY-S` or `JGLEDT-SCRNCH-BTF-BLK-L`. Anything with fewer segments, a missing hyphen, or a lowercase segment is a finding. `JGLEDTABY-BLM-WTE-L` sat malformed for months and was silently excluded from a catalogue query that filtered on the correct prefix — a filter that drops rather than errors hides exactly this.

## Step 4 — Check whether new tags or collections are needed

This is the part that keeps the system alive rather than merely tidy. Ask:

**New tag values?** Scan for products whose title, handle or description implies a facet value not in the standard — a print name that doesn't exist yet, a silhouette the vocabulary doesn't cover, a colour shade with no family mapping. New drops are the usual trigger.

**New collections?** A tag earns a collection when enough products carry it to make a page worth having — roughly 5+ — and it's a way a customer would actually shop. Check both directions:

- Tags with meaningful coverage and no collection → propose creating one.
- Manual collections whose membership now matches a tag exactly → propose converting them to smart collections, so they maintain themselves.
- Collections that are empty, duplicated, or unpublished orphans → propose cleanup.

**On visibility:** publishing a collection to a sales channel and adding it to the navigation menu are separate controls. Structural collections — ones that exist to shape recommendations rather than to be browsed, like `Modest Wear` — should be **published but not added to navigation**. Published makes them function; unpublished makes them invisible to the storefront and useless as a recommendation signal. Say which you're proposing for each collection.

## Step 5 — Rotate the badges

Every product has a `custom.badges` metafield — type `list.single_line_text_field`, so the value is a JSON array of strings.

**The vocabulary is a single value: `Lumi's Favs`.** Reproduce it character for character — the apostrophe, the capital F. Themes typically style badges by matching the exact string, so a near-miss like "lumi's favourites" renders as an unstyled badge or nothing at all, and you end up with two labels meaning the same thing.

A `Low in Stock!` badge was previously in use and was **deliberately retired in August 2026**. Do not reintroduce it, and don't propose a low-stock badge as an improvement — scarcity messaging was a considered decision to drop, not an oversight. If it reappears on a product, that came from outside this process; flag it for removal.

### Picking Lumi's Favs

The goal is that every collection page a customer can browse has a couple of badged products on it, so no page looks unmerchandised.

1. List every collection published to the Online Store with at least one product.
2. For each, pick **2 products** to carry `Lumi's Favs`.
3. Prefer **high stock**. A badge drives attention, and pointing attention at a product with one unit left produces a sold-out click. Deep stock is the primary criterion.
4. Spread the picks. A product already badged for one collection still counts toward another collection's two, so favour products that fill an otherwise empty page.
5. **Rotate.** Products badged in the previous run should generally step aside unless they're the only sensible option — a badge that never moves stops meaning anything.
6. Skip anything sold out or negative-stock entirely.

### Writing badges safely

The metafield is a **list**. Writing a value replaces the whole array — so read the existing value first and write back the full intended list, or you'll silently drop a badge the product already had.

## Step 6 — Report and ask

Write the findings as a markdown file and deliver it with `SendUserFile`.

Khaled often reads this on a phone. Lead with the summary, keep tables narrow, and don't make him scroll through 90 rows of bucket A to find the three decisions that need him.

Use this structure:

```
# PRNTCODE Catalogue Review — [Month Year]

## Health summary
[One paragraph: how many products are fully compliant, what moved since last month,
and the single most important thing to fix.]

## A — Safe to apply (N changes)
[Table: Product | Change. Collapse repetitive rows — "12 RTW products: add Silk" beats 12 lines.]

## Variant structure (N findings)
[Size values, colour casing, missing barcodes, SKU shape. Say which bucket each belongs to —
colour option values are always C because they are customer-visible swatches.]

## B — Corrections (N changes)
[Table: Product | Current | Proposed | Why]

## C — Needs your decision (N items)
[One short section each. State the options and give a recommendation.]

## New tags or collections proposed
[What's missing and why it's worth creating. Say published-but-unlinked or in-navigation.]

## Badge rotation
[Table: Collection | Products picked | Stock | Replacing]

## Nothing changed yet
[Explicit line confirming Shopify is untouched and what happens on approval.]
```

Then use `AskUserQuestion` to ask what to apply — offer applying A and B, A only, everything including the C decisions, and let him decline. If `AskUserQuestion` isn't available, ask in plain text.

## Step 7 — Apply, then verify

Only after approval. Use `tagsAdd` / `tagsRemove` for tags, `metafieldsSet` for badges, `collectionCreate` / `collectionUpdate` for collections. Validate every mutation with `validate_graphql_codeblocks` before running it.

**Verify by querying products by ID, not by `tag:` search.** Shopify's search index lags behind writes by several minutes, so a `tag:` query run straight after a write will report the old state and look like a failure. This has already caused one false alarm — check the product record itself.

Report exactly what changed, and flag anything that didn't apply.

## Step 8 — Update the standard

If the review surfaced new prints, colours, silhouettes, collections, or resolved an open question, update `claude/prntcode-product-tag-standard.md` via `project_write` — read it, edit it, write the full updated content back to the same path. There's no partial edit.

Note the review date and what changed at the top. The next run reads this document as its source of truth, so an unrecorded decision is a decision that gets re-litigated every month.

---

## Reference

`references/graphql-recipes.md` — tested queries and mutations for catalogue pull, badge read/write, collection creation, and verification. Read it in step 2 rather than composing queries from scratch.
