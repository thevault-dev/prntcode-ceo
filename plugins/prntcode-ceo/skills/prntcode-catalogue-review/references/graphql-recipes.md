# GraphQL recipes — PRNTCODE catalogue review

All of these run through the Shopify connector's `graphql_query` / `graphql_mutation` tools against the Admin API. Every one has been run successfully against the PRNTCODE store.

Validate mutations with `validate_graphql_codeblocks` before executing. It catches invented field names, which is the usual failure.

## Contents

1. Full catalogue pull (paginated)
2. Product count sanity check
3. Badge metafield read
4. Badge metafield write
5. Collections with rules and publication status
6. Create a smart collection
7. Add / remove tags
8. Verification by ID

---

## 1. Full catalogue pull (paginated)

Do **not** use the `search_products` tool for this — its output exceeds the token limit and truncates silently. Page at 50 until `hasNextPage` is false.

```graphql
query($after: String) {
  products(first: 50, after: $after, sortKey: CREATED_AT, reverse: true) {
    pageInfo { hasNextPage endCursor }
    edges {
      node {
        id title handle productType status tags totalInventory
        options { name values }
        priceRangeV2 { minVariantPrice { amount } }
        metafield(namespace: "custom", key: "badges") { value type }
      }
    }
  }
}
```

Pass the previous response's `endCursor` as the `after` variable. Requesting more fields than these (descriptions, media, full variants) risks truncation — pull extra detail per-product only where a finding needs it.

## 2. Product count sanity check

Run first so you know how many pages to expect.

```graphql
query { productsCount { count } }
```

## 3. Badge metafield read

The definition is `custom.badges`, type `list.single_line_text_field`. The value is a **JSON-encoded array of strings**, e.g. `"[\"Lumi's Favs\"]"`.

```graphql
query($id: ID!) {
  product(id: $id) {
    title totalInventory
    metafield(namespace: "custom", key: "badges") { value type }
  }
}
```

`null` means no badges set — which is different from an empty array.

## 4. Badge metafield write

Writing replaces the entire list. Read the current value first and write back the full intended array, or existing badges get dropped.

```graphql
mutation SetBadges($metafields: [MetafieldsSetInput!]!) {
  metafieldsSet(metafields: $metafields) {
    metafields { key value }
    userErrors { field message code }
  }
}
```

Variables — note `value` is a JSON string, not an array:

```json
{
  "metafields": [
    {
      "ownerId": "gid://shopify/Product/10340215816484",
      "namespace": "custom",
      "key": "badges",
      "type": "list.single_line_text_field",
      "value": "[\"Lumi's Favs\"]"
    }
  ]
}
```

To clear badges, use `metafieldsDelete` rather than writing `"[]"` — an empty array can still render an empty badge container in some themes.

`metafieldsSet` accepts up to 25 metafields per call. Batch accordingly.

## 5. Collections with rules and publication status

`publications` being empty means the collection is published nowhere — invisible to the storefront and useless as a recommendation signal.

```graphql
query {
  collections(first: 50) {
    edges {
      node {
        id title handle sortOrder
        productsCount { count }
        ruleSet { appliedDisjunctively rules { column relation condition } }
        publications(first: 5) { edges { node { publication { name } } } }
      }
    }
  }
}
```

`appliedDisjunctively: true` means the rules are OR'd; `false` means AND.

Note: `publishedOnCurrentPublication` requires the `read_product_listings` scope and will error — use `publications` instead.

## 6. Create a smart collection

```graphql
mutation CreateCollection($input: CollectionInput!) {
  collectionCreate(input: $input) {
    collection { id title handle }
    userErrors { field message }
  }
}
```

Variables — a two-rule OR collection, as used for `Modest Wear`:

```json
{
  "input": {
    "title": "Modest Wear",
    "descriptionHtml": "",
    "ruleSet": {
      "appliedDisjunctively": true,
      "rules": [
        {"column": "TAG", "relation": "EQUALS", "condition": "Full Coverage"},
        {"column": "TAG", "relation": "EQUALS", "condition": "Modest"}
      ]
    }
  }
}
```

Creating a collection does **not** publish it and does **not** add it to navigation — those are separate. Adding to a menu is a manual step in Shopify admin; tell Khaled when a collection needs it, rather than assuming it's done.

Tag matching in collection rules is case-insensitive, which is why the existing `latest` rule still catches products tagged `Latest`. Don't rely on that — it's fragile.

## 7. Add / remove tags

```graphql
mutation AddTags($id: ID!, $tags: [String!]!) {
  tagsAdd(id: $id, tags: $tags) { node { id } userErrors { field message } }
}
```

```graphql
mutation RemoveTags($id: ID!, $tags: [String!]!) {
  tagsRemove(id: $id, tags: $tags) { node { id } userErrors { field message } }
}
```

For several products at once, alias them into one mutation rather than making one call each:

```graphql
mutation Multi($a: ID!, $b: ID!, $tags: [String!]!) {
  r1: tagsRemove(id: $a, tags: $tags) { node { id } userErrors { field message } }
  r2: tagsRemove(id: $b, tags: $tags) { node { id } userErrors { field message } }
}
```

## 8. Verification by ID

**Do not verify with `tag:` search.** Shopify's search index lags writes by minutes and will report the pre-write state — that looks like a failed mutation when nothing is wrong.

```graphql
query {
  a: product(id: "gid://shopify/Product/111") { title tags metafield(namespace: "custom", key: "badges") { value } }
  b: product(id: "gid://shopify/Product/222") { title tags metafield(namespace: "custom", key: "badges") { value } }
}
```

Sample five changed products across different change types rather than checking all of them.

---

## Known store facts

- Store: PRNTCODE, `www.prntcode.com`, Basic plan, AED, timezone UTC+4.
- Badge vocabulary in live use: `Lumi's Favs` only. `Low in Stock!` was retired Aug 2026 — do not reintroduce.
- Badge metafield definition ID: `gid://shopify/MetafieldDefinition/215869522212`
- `Shop All` uses the handle `all`, which Shopify's recommendation algorithm ignores by design.
- `APPPlaza - Best Sellers` is an orphan from an uninstalled app — published to zero channels, rule `price > 0`, contains everything. Harmless; safe to delete.
- Search & Discovery metafields exist on this store (`shopify--discovery--product_recommendation.related_products` and `.complementary_products`, max 10 each) — these are the route to deterministic per-product recommendations if tag-driven collections aren't precise enough.
