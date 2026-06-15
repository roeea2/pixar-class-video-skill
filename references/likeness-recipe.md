# Likeness Recipe

The #1 thing users care about: **the character must look like the real child.**
Generic "cute cartoon kid" output is a failure. Use this every time you build a
character sheet.

## The prompt formula

State, explicitly:
1. **Real age**, framed against the toddler default: `"about 12 years old, a
   preteen, NOT a young child"`.
2. **Face shape** named precisely: e.g. `"a LONG, NARROW face with a slim
   jawline"` / `"a round full face"` / `"a heart-shaped face"`.
3. **Exact hair**: length, texture, color, parting/updo — `"shoulder-length wavy
   dark-brown hair parted on the side"`.
4. **Eye color** explicitly (the model drifts to brown) — `"clearly BLUE eyes,
   NOT brown"`.
5. **Distinguishing marks**: freckles, glasses, dimples, a necklace, etc.
6. **Stylization limiter**: `"only mild Pixar stylization that preserves the real
   facial structure — not a generic cartoon child."`

Always add for solo shots: **"Exactly ONE child alone, no other people."**

## What NOT to say

- ❌ "big expressive eyes", "soft rounded features", "adorable" → these collapse
  every face into the same toddler-ish look.
- ❌ "diverse" in any crowd prompt (see prompt-gotchas).

## Reference images

- Crop the face tightly (square, centered) from the child's `self` photo and pass
  it as the identity reference.
- Build a clean **character sheet** first (front + 3/4 view, neutral background).
  Approve it, then **seed every scene for that child from the approved sheet** so
  they stay consistent across all their clips.
- If the child supplies their OWN stylized character (some do), use it directly as
  the identity reference and do NOT re-derive from the photo — it will match what
  they expect far better. (Real example: a teacher kept rejecting photo-based
  renders until she handed over her own Pixar portrait; using it as the ref ended
  the back-and-forth instantly.)

## Verify, every time

Render the sheet, **show it to the user**, and ask "does this look like <name>?"
Re-roll on request. Cheap to fix here; expensive after you've built 3 scenes.

## Model choice

- `nano_banana` (Higgsfield's nano_banana_pro → nano_banana_2) keeps the Pixar
  look and accepts ≥4 image references. Default for this pipeline.
- Photoreal models give better likeness but lose the animated style — rejected for
  this use case. Keep the Pixar look and push likeness via the prompt + refs.
