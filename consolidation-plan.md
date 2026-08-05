# Site Consolidation — Corrected Findings & Final Plan

Date: 2026-08-03
Supersedes: Hermes's `summary.md` draft (§0's repo-identity claim was wrong; see below)

## The correction that changes everything

Hermes's draft claimed tnkb and tenniskb are "the same repo, different subpath," and built the whole plan on that. **They are not.** I checked the actual git remotes on every local clone plus `git ls-remote`/blobless clones of the real org repos directly. Ground truth:

| Site | Real repo | Branch | Theme | Structure |
|---|---|---|---|---|
| **tnkb** | `tenniskb/tnkb` (org) | `main`, HEAD `b3ce2c1c` | Material, **green/light-green**, `custom_dir: overrides` | Real MkDocs source. `docs/{foundation,advanced,elite,handbook,players,science-lab,system,vi}/`. `site_url: https://tenniskb.github.io/tnkb/` |
| **tenniskb** | `tenniskb/tenniskb` (org) | `main`, HEAD `60d91595` | Custom hand-built (own `stylesheets/`) | **Not MkDocs** — 1,111 hand-authored static HTML files. `about/ assess/ mental/ membership/ patterns/ physical/ resources/ start-here/ strokes/ system/ en/ vi/`. `main` and `gh-pages` are nearly identical (diff = only generated asset hashes + `.nojekyll` + 2 workflow files) — **no rebuild-vs-hand-sync risk, `main` already is the maintained source.** |
| **tennis-unified** | `tenniskb/tennis-unified` | `main`, HEAD `8ec4f858` (this session's push) | MkDocs Material, teal/blue | 1,495+ md, `use_directory_urls: false` |

**What Hermes actually analyzed as "tnkb":** the local folder `C:\Users\Henry\Documents\GitHub\tenniskb` is a clone of `henryPhamDuc/tenniskb` — a **personal-account repo, not part of the `tenniskb` org at all**, and not the same content as `tenniskb/tnkb`. Every claim in Hermes's §3 (teal/blue theme, `custom_dir: docs/theme`, 71 nav_translations, Foundation/Advanced/Elite tiers matching tennis-unified) describes this wrong repo. It should be dropped from the consolidation entirely — it's not one of the three target sites.

**Also corrected:** the two local clones Hermes found for "tenniskb" (`tenniskb-repo` at `fa37560`, `tenniskb-account/tenniskb-target` at `c6d5446`) are both genuinely `tenniskb/tenniskb`, just stale — both need `git pull` to reach current HEAD `df32013`/`60d91595`. There is no separate "source vs. build artifact" distinction for this site like Hermes assumed; it was never MkDocs to begin with.

## Decisions (made, not left open)

1. **URL scheme:** tennis-unified's `use_directory_urls: false` stays canonical. tnkb's mkdocs content gets rebuilt with that flag when ported in (it's a config flip + rebuild, not a rewrite).
2. **CSS/theme:** three sites, three different palettes (teal/blue, green, tenniskb's own). No re-theme in this pass — each ported tier keeps functioning with its own CSS on the way in; a single unified palette is a later, separate decision, not a blocker for consolidation.
3. **tnkb nav translations:** port the real `tenniskb/tnkb` mkdocs.yml's nav translation block over (need to re-check the actual count now that we're looking at the right repo — Hermes's "71 entries" was from the wrong repo too).
4. **Where tnkb/tenniskb content lands — RESOLVED, no conflict to manage:** I checked tennis-unified's actual current `docs/` tree directly. There is **no** `03-foundation`, `04-advanced`, or `05-elite` folder — those tiers don't exist here. (An earlier session's plan, in `Tennis Library.md`, intended to port tenniskb's Foundation/Advanced/Elite content in, but it never actually landed — or it landed and was later removed. Either way, current state has zero overlap.) This means tnkb's 156 files (`foundation/`: 104, `advanced/`: 24, `elite/`: 28, under `docs/`) can be added as new top-level tiers directly — no diff-and-pick-winners step needed, no risk of clobbering existing content. Land them as `docs/foundation/`, `docs/advanced/`, `docs/elite/` (numbered to fit the existing `01-08` sequence, e.g. `03-foundation/04-advanced/05-elite`, renumbering `03-stroke-analysis` etc. up as needed) with `use_directory_urls: false` applied on the way in. Same story for `tenniskb`'s content — nothing in tennis-unified currently resembles its `about/assess/mental/patterns/physical/strokes/system` structure, so it's a pure add, not a merge.
5. **tong-ket.md, the 5 modified files, favicon:** already resolved last round — delete the orphan, discard the 5 stale local edits, keep the favicon as-is.

## Hermes: mechanical task list (heavy lifting, no judgment calls)

Run these against the **correct** repos this time — `tenniskb/tnkb` and `tenniskb/tenniskb`, not the `henryPhamDuc/tenniskb` personal clone:

1. `git pull` both `tenniskb-repo` and `tenniskb-account/tenniskb-target` to sync to current `tenniskb/tenniskb` HEAD (`60d91595`/`df32013`).
2. Clone `tenniskb/tnkb` fresh (there's no correct local clone of it yet — use `--filter=blob:none` if the plain clone times out, it works fine).
3. In the fresh `tnkb` clone: dump the actual `mkdocs.yml` nav tree and `nav_translations` block to a file for review (don't port it yet, just extract it).
4. ~~Overlap diff~~ — already confirmed unnecessary: tennis-unified has no `foundation/advanced/elite` content at all (I checked directly), so tnkb's 156 files there are a pure add, not a merge. Skip straight to staging the copy: `docs/foundation/` → `docs/03-foundation/`, `docs/advanced/` → `docs/04-advanced/`, `docs/elite/` → `docs/05-elite/` (renumber tennis-unified's existing `03-stroke-analysis`→`06-`, `04-new-issue`→`07-`, `08-reference-library`→`08-` stays, `09-tennis-wiki-reference`→`09-` stays, etc. — keep it sequential). Same for tenniskb's `about/assess/mental/membership/patterns/physical/resources/start-here/strokes/system/en/vi/` — no existing equivalent in tennis-unified, straight add as its own tier(s). Stage locally, do not push.
6. In `tennis-unified`: `git checkout -- docs/reference-library/tennis-books/1-absolute-tennis-clean.md docs/reference-library/tennis-books/1-absolute-tennis-structured.md docs/reference-library/tennis-books/1-absolute-tennis-final-vi.md docs/reference-library/tennis-books/step-by-step-cleaned.md docs/reference-library/tennis-books/step-by-step-raw.md` (discards stale drift), then delete `docs/reference-library/tennis-books/cam-nang-quan-vot-toan-dien/tong-ket.md`.
7. Note for git writes: plain `git add`/`git commit` hung indefinitely on this machine's `tennis-unified` mount earlier this session (40s+ for even trivial commits). Working fix, use it directly instead of retrying plain commit:
   ```bash
   export GIT_INDEX_FILE=/tmp/scratch_idx
   git read-tree HEAD
   git add <paths>
   TREE=$(git write-tree)
   COMMIT=$(git commit-tree "$TREE" -p "$(git rev-parse HEAD)" -m "...")
   git update-ref refs/heads/main "$COMMIT"
   unset GIT_INDEX_FILE
   git push origin main
   ```
   Don't push without Henry's sign-off per his stated workflow — stage/commit locally and report back, or push only the housekeeping items in task 6 (already agreed, low-risk).

None of the above requires a content judgment call — it's extraction, diffing, syncing, and previously-agreed cleanup. **Do not port or merge any tnkb/tenniskb content into tennis-unified yet** — that step needs the real overlap report (task 5) reviewed by a human/intelligence pass first, same mistake Hermes was about to make by planning Step 4 on top of an unverified premise.
