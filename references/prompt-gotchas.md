# Prompt Gotchas & Fixes

Real failure modes seen building a full class movie, with the exact fix.

## 1. False "NSFW" flag on a child image
nano_banana sometimes flags a perfectly innocent child sheet/scene as NSFW.
**Fix:** rephrase to wholesome framing —
`"a wholesome Pixar-style 3D animated movie character of a cheerful
schoolchild..."` and retry. It clears.

## 2. Random dark-skinned filler people in crowd/group scenes
Crowd prompts inject random people who don't match the class.
**Fix:** (a) remove the word **"diverse"**; (b) state the class's actual look
explicitly, e.g. `"Israeli schoolchildren with fair to light-tan skin, none
dark-skinned"`; (c) if it persists (pools/wide shots), add a second pass `"do NOT
include any dark-skinned characters"`. Seed 4–6 distinctive character refs so real
kids anchor the crowd.

## 3. The same person duplicated in frame
**Fix:** `"Exactly ONE child alone, no other people."` For multi-kid scenes,
describe each by a distinguishing feature (glasses / dark wavy hair / denim
jacket) instead of a count.

## 4. Character comes out heavier / rounder than the child
A too-strong "sturdy/round" character ref makes the model render them fat in group
scenes.
**Fix:** drop that child's ref in the group shot, keep a light identifier (cap +
shirt color), and add `"slim, average build"`.

## 5. Braces / wrong teeth
**Fix:** `"clean natural white teeth, NO braces."`

## 6. Wrong eye color
The model drifts to brown.
**Fix:** name it — `"clearly BLUE eyes, NOT brown"` — and verify on the render.

## 7. Subject too dark
Golden-hour / backlit prompts darken skin unrealistically.
**Fix:** `"bright even midday daylight, natural skin tone, not dark."`

## 8. Unnatural action (e.g. a ball teleporting to the hand)
For sports/action, describe the physical reality precisely: `"the ball rests on
the ground at his feet; he kicks the SINGLE ball forward, never to his hands."`
Give the animation a clean start frame that matches.

## 9. Group likeness ceiling
At ~10+ faces the model cannot keep every face exact. Set expectations: seed the
most distinctive refs, accept "a lively, believable class crowd" for big group
shots, and keep exactness for the solo scenes.

## 10. Spurious preset recommendations
The video tool may suggest an unwanted "preset" (e.g. a music-themed one) for
cheerful/crowd scenes. Pass that preset's id as `declined_preset_id` on the retry.

## 11. Transient failures
Occasional `failed`/slow jobs are normal — just retry the same call.
