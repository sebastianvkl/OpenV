# Product image provenance

The README and website share the optimized image files in [`web/public/images/`](../../web/public/images/). They are captures of OpenV's actual browser application, not generated product mockups.

| File | What it shows | Engineering source |
|---|---|---|
| `hero.webp` | Assembled CAD candidate and recorded verdict totals | `run-365c68904f40`, design `design-34c4fb0ecbe1` |
| `flight.webp` | Aircraft in the interactive flight environment | Same run/design; computed response with illustrative scenery |
| `assembly.webp` | Actual STEP imported and exploded in the browser | Same run/design, 45 named parts |
| `social.png` | Share card made from the hero capture and OpenV text | Same CAD capture; typography/layout only |

Captured on 2026-09-08. The case-study text links `run-dcef3705d89d`, the preceding actual Astra collision-repair run. The screenshot run re-verifies that unchanged repaired candidate and adds point-mass response artifacts. Do not relabel a screenshot as a different design or as physical flight evidence.

These images show OpenV-generated aircraft geometry and application UI. Purchased bodies remain envelopes. Manufacturer reference photos in the interactive component panels are separately attributed and are not presented here as OpenV-authored vendor CAD.

To refresh the images, load the identified public run, capture a desktop viewport, retain all scope/status labels, and export a compressed WebP. A changed design or scenario needs an updated source entry. Update the shared files once; both README and site consume the same assets.

The OpenV mark and wordmark are editable SVGs in `web/public/brand/`, drawn for this project. The mark follows the engineering V with a distinct return path and evidence node. The interface uses navy `#15283f`, cool paper `#f0f3f8` and orange `#d95024`; PASS, FAIL and UNKNOWN keep their own labeled status colors. Screenshots and the share card were refreshed with this identity.
