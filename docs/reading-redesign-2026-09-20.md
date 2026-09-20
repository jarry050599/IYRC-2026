# LinkGuard research reading redesign — 2026-09-20

This follow-up redesign builds on commit `0685d3091d8a7b4072405f07abebaf7c2481d997` and supersedes the page layouts described in the initial UI redesign notes. The objective is to retain the complete research while making the system, evidence and engineering documentation easier to understand.

## Scope and preservation

- All 14 existing pages and their URLs remain available under the original SYSTEM / RESEARCH / EXPLORE structure.
- All 2,807 original non-empty main-content text nodes are retained. Original anchor IDs and link destinations are retained, with no duplicate IDs.
- Original inline and external script tags are byte-identical, apart from the addition of the presentation-only `reading-experience.js` reference. Existing language, modal, media, simulation, disclosure and routing handlers remain intact.
- Backend, API, data structures, algorithms, research figures, firmware and route mapping are unchanged.
- New summaries repeat existing evidence and limitations; new headings, outlines and visual labels organize the original material.
- The requested Apple Design Skill was unavailable in the connected catalog. The implementation follows the user's supplied Apple HIG design principles; it does not claim use of an unavailable skill or an Apple certification.

## Shared visual and reading system

`design-system.css` supplies the existing shared tokens. `reading-experience.css` is the final presentation layer for this pass, and `reading-experience.js` manages only reading and navigation state.

| Area | Contract |
| --- | --- |
| Typography | Apple system stack, `system-ui`, Traditional Chinese system fallbacks; one shared Chinese/English type system |
| Scale | Responsive display and headings, 16px body, 12–14px metadata, 48–72px desktop metrics; smaller controlled mobile metrics |
| Technical text | System monospace stack, 14px code, keyboard-scrollable code examples |
| Colors | `#FFFFFF`, `#F5F5F7`, `#1D1D1F`, restrained `#0066B5` action blue; status colors retain their existing meaning |
| Spacing | Shared 8 / 12 / 16 / 24 / 32 / 48 / 64 / 80 / 96 / 120px rhythm, maximum content width 1120px |
| Surfaces | Open sections and dividers; contained surfaces only for genuine grouping; controlled 10 / 16 / 24px radii |
| Navigation | Three grouped desktop menus; compact-screen drawer with backdrop, focus containment, Escape handling and inert background |
| Reading | Local page outlines, engineering sidebar, large qualified metrics, native research disclosures and existing specification controls |
| Motion | Short ease-out highlights and disclosures; continuous diagram packets hidden; reduced-motion preference respected |
| Accessibility | Visible focus, labelled controls, semantic headings and lists, touch targets, readable contrast and keyboard-accessible scrolling |

The legacy `multipage.css` home-section filter now allows the new home reading sections. The versioned reading stylesheet also overrides the earlier cached filter, so mixed cached styles cannot hide the new chapters. The service worker cache changes from v24 to v26 and includes the two new presentation files; its lifecycle and fetch logic are unchanged.

## Page changes

| Page | Reading experience |
| --- | --- |
| Home | Exact existing title/subtitle; compact system diagram; Problem → Solution → Workflow → Evidence → System → Team/Awards; real hardware photography below the introduction |
| Overview | Readable report width, chapter links and evidence labels on existing metrics |
| Background | Clear problem and motivation outline, original narrative and facts retained |
| System | Victim → Sensor Node → LoRa → Command Center → Rescue Team before hardware; Wide → Close → Ground search layers; visible real hardware photos and progressive specifications |
| Functionality | SENSE → SEND → SEARCH → DECIDE → DISPATCH; hover/focus previews the matching nodes and paths, click retains selection; the original three-step controls remain usable |
| Data | Research dashboard with measured link range and separately qualified battery, capacity and vehicle estimates; all original tables remain below |
| Experiments | Each experiment begins with Question / Method / Result / Interpretation; original methods, tables, figures, theory, questions and references remain in expandable sections |
| Development story | Chapter outline and original development timeline/disclosures |
| Comparison | Three clearly titled comparison tables, generous row spacing, sticky first column and independently scrollable mobile regions |
| Field | Gallery/video outline with existing photography, carousel, lightbox and video player |
| Technical | Sticky document outline, firmware section initially open, complete code/packet/frequency/workflow/hardware/software material; outline links reveal their target panels |
| Deployment | 1 Team → 10 / 40 / 100 Nodes → Township progression; cost bars use the original estimates; full design-scenario assumptions and exclusions remain visible |
| Team | Research-team presentation with consistent portraits, names and roles; responsibilities visible without expansion, original quotes and social controls accessible through the existing disclosure |
| Awards | Research-milestone timeline, certificate disclosures and a gallery using the actual IYRC trophy/certificate photograph; original event photographs and carousel retained |

## Evidence provenance

These distinctions are explicit next to highlighted values, rather than inferred from decorative colors:

| Figure | Qualification |
| --- | --- |
| 900 m | Measured interference-site communication range; not an established buried-victim detection range |
| 1.96 km | Maximum communication distance across the four existing range tests |
| 3.0% / 63 dB | Saline laboratory model, 15cm water layer; not a direct reinforced-concrete field measurement |
| ≈2.9 floors | Conceptual equivalent-floor upper-bound estimate, not a measured building result |
| 91.54% / +25.85pp | Rescue-efficiency simulation, 1,000 paired Monte Carlo trials; not observed field rescue performance |
| 120h, UGV 40min, fixed-wing 8km/40min, quad 1.5km/15min | Design estimates, retaining the original conditions |
| 40 / 55 tracked nodes | Capacity estimate, stable / peak |
| NT$20,000 / 80,000 / 200,000 | Original 10 / 40 / 100 node cost scenarios; exclusions retained; these do not imply 100-node measured concurrent capacity |

## Verification

- All 14 routes checked at 1440, 820, 390 and 320px. Final page layouts have no uncontained horizontal overflow or JavaScript runtime errors. Intrinsically wide tables, diagrams and code scroll inside their own regions.
- All routes checked in English at 390px; the new complete home layout additionally checked in both languages at all four widths, including its tooltips.
- Expanded system specifications, experiments, technical documentation, story, team and certificate sections checked at 1440, 390 and 320px.
- Desktop, tablet and mobile screenshots inspected, including large metrics, full experiment methods, packet examples, sticky comparison labels, costs, team quotes, certificate photos and the drawer.
- 28 existing interaction/keyboard checks and 20 reading-experience checks passed. Coverage includes language persistence, skip link, menu and modal focus, system disclosure, SOS architecture demonstration, flow controls, research disclosures, media, comparison scrolling and legacy fragment redirects.
- axe-core WCAG 2 A/AA and WCAG 2.1 AA checks passed on all 14 initial page states, all six expanded-content page types, and the open mobile drawer. Reference-link contrast, code-comment contrast, technical-note contrast and keyboard code scrolling were corrected during expanded-state verification.
- Preservation comparison: 14/14 pages retain every original main-content text node, anchor ID, link destination and original script tag. No duplicate IDs.
- JavaScript syntax and Git whitespace checks passed.
- v26 offline cache verified for the home and technical routes, including the new visual layer.

Tests used Chromium on Linux. Safari/iOS and physical rescue hardware were not tested. Automated accessibility checks are not a complete accessibility certification.

## Real assets and missing certificates

The existing product, sensor, vehicle, field, team and award photographs are retained. No generated hardware, certificates or award evidence was introduced. No dedicated fixed-wing photograph exists in the current assets, so no substitute image is presented as that aircraft.

Seven individual certificate scans are absent from the repository. Their existing placeholder copy and intended file paths are retained in the certificate disclosures. Absent files are no longer requested as broken images. The gallery instead displays the verified existing `assets/awards/photos/iyrc-2026-03.jpg` trophy/certificate photograph, without claiming it replaces the missing individual scans.
