# LinkGuard — 921 Memory Edition refinement

Date: 2026-09-20

## Scope

Refine the existing fourteen-page frontend and add a homepage-only digital memorial introduction. This is an incremental update to the existing 921 archive design. Backend, APIs, research methodology, numerical results, application algorithms, routes and existing application scripts are unchanged.

## UI changes

- Complete the shared paper/white/ink palette, with secondary surface `#E9E5DD`, a 10% ink divider, restrained archive red and muted gold.
- Define twelve typography roles: display, hero, H1, H2, H3, body, small, caption, metric, label, navigation and technical. Retain system typography, Traditional Chinese fallbacks, the shared spacing scale and monospaced metadata.
- Refine the Chinese/English segmented control and grouped navigation hover treatment.
- Reorder existing home sections into memory, problem, lesson, engineering, LinkGuard, evidence and future. Retain every original section, anchor and passage.
- Add a six-stage system reading path: Sense, Connect, Locate, Command, Search and Confirm. Each stage opens or reaches the corresponding original material. The original node/data path remains in a native disclosure and at its original anchor.
- Add restrained field-operation, development, comparison and deployment record labels. Keep measured, simulated and estimated evidence labels intact.
- Unify team portraits at 4:5 and label existing research responsibilities.
- Group awards with explicitly recorded 2026 dates. Other awards retain their source details and clearly indicate that no year was supplied. Do not infer dates or manufacture certificates.
- Retain all real photographs, engineering diagrams, research tables, formulas, limitations and technical disclosures. No generated historical image or certificate is added.

## Digital memorial introduction

The homepage loads `memorial-intro.css` and `memorial-intro.js`. A native modal `dialog` covers the viewport with the paper background. It presents the 1999 date, archive number, large 921, remembrance text and a quiet LinkGuard signature.

- Year count is computed from the current local year minus 1999; Chinese and English wording update together.
- Entrance uses opacity only and completes in 1,550 ms. Exit crossfades into the homepage over 500 ms, with a 600 ms event fallback.
- The close icon, Enter LinkGuard button and Escape all dismiss without navigation or reload.
- The second-stage refinement restores first-visit behavior, following the latest request. The original `linkguard-921-intro` key stores `seen` on Enter, close or Escape. Refreshes and new tabs then skip the introduction. The original sessionStorage fallback is retained only when localStorage is unavailable; no second key is introduced.
- Native modal background inertness, explicit focus containment, visible keyboard controls and focus restoration protect keyboard navigation. The dialog has a labelled title/description and `aria-modal="true"`.
- The existing language handlers serve the introduction's segmented control; no duplicate language state is introduced.
- Reduced motion removes entrance staging and closes immediately.
- Mobile uses `100dvh`, safe-area padding, 44 px language/close controls and a 48 px entry button (44 px on short screens). Short landscape screens scroll within the dialog while the close control stays accessible.
- The service-worker cache is updated to v33 and both introduction assets are versioned `921-4`. Its install/fetch behavior is unchanged.

To test a fresh visit, run `localStorage.removeItem('linkguard-921-intro')` and reload. If localStorage is blocked and the original session fallback is active, remove the same key from sessionStorage instead.

## Validation

Baseline: commit `1e6c0440ddfcba23d18eed9b570e4af00506f02b`.

- All 3,594 original main-content text nodes across fourteen routes are retained. Existing IDs, links and image references are retained. Every original script block is preserved byte-for-byte.
- All fourteen routes checked at 1440, 820, 390 and 320 px (56 route/viewport combinations): no unintended horizontal overflow, missing resources, undersized text findings or page runtime errors. English checked on every mobile route.
- The original refinement passed forty-three memorial checks, including the former first-visit persistence behavior. The follow-up frequency change removes that persistence; the introduction now appears on every homepage load while retaining its existing close, language, motion and keyboard behavior.
- Original navigation, contact dialog, hardware disclosures, architecture simulation, functionality steps, experiment and technical accordions, story and team disclosures, photo lightbox, carousels, comparison keyboard scrolling and legacy bookmarks were exercised successfully.
- All six new operation links reach the original content and open specifications where applicable. The original system-overview bookmark still opens the retained node path.
- Fifty-seven referenced local image/PDF URLs return successfully; the proposal has a valid PDF signature. Existing unavailable certificate slots remain explicit placeholders.
- Automated WCAG A/AA checks report no violations on fourteen page views, the expanded research/technical/system/team views, the navigation drawer and the introduction in both languages. Keyboard checks complement the automated scan; this is not a claim of a formal accessibility certification.
- Desktop/mobile screenshots reviewed for all fourteen pages and detailed system, metric, technical, comparison, team and certificate sections.
- Offline home and technical route verified with the updated cache.

Validation uses Chromium desktop/mobile viewport emulation. Physical-device or Safari validation is not claimed.

## Homepage opening consolidation

The 921 historical opening and LinkGuard system introduction now form one `#top` header. The existing `#linkguard-now` anchor moves inside that opening, ahead of the problem, timeline and workflow sections. Desktop places LinkGuard on the left and the 921 memory narrative on the right, with the communication diagram and map aligned below their respective columns; mobile presents the product first. The original map, source captions and communication diagram remain visible in a supporting row within the same opening.

The system title becomes the page H1 and the historical title becomes an H2. All original text, IDs, links, image sources and scripts are retained. The independent `home-hero.css?v=921-5` stylesheet applies only to this opening; the service-worker cache advances to v31. The memorial continues to appear on every homepage load.

The combined opening was reviewed in Chinese and English at 1440, 1280, 820, 390 and 320 px, including a 320 × 568 viewport. The brand and primary action fit in the initial viewport. Existing anchors, contact controls, research navigation and the mobile drawer were exercised; no new runtime errors or automated accessibility violations were found.

The desktop column reversal was checked again in both languages at all five viewport widths. The directional link points toward LinkGuard, mobile ordering is retained, and no horizontal overflow, runtime/resource errors or automated accessibility violations were found. This follow-up changes only homepage layout CSS and cache versions.

## Redundant introduction link

Removed the Chinese/English “Explore today’s rescue technology” link, its arrow and underline at the user’s request. LinkGuard is already beside the memory narrative, so the internal jump is unnecessary. The `linkguard-now` target remains available; all other text, links and JavaScript are unchanged. Removed the unused homepage arrow overrides and updated the homepage stylesheet to `921-6` and service-worker cache to v32.

## Second-stage memorial refinement

Refined the existing native dialog only. The date, archive index, 921, bilingual title, remembrance text and signature have separate typographic levels. The title presents Chinese above smaller English supporting text, with explicit language attributes. The body remains under the original language switch with block-level translations. All memorial wording and meaning are preserved. Two faint registration marks provide an archival reference without new images or invented metadata.

The existing script now executes immediately after the dialog markup, before homepage controls parse, preventing a homepage flash even when the script is delayed. Its initial language matches the existing `lg-lang` preference; the original page handlers still own language changes. Native modal inertness, focus containment and scroll locking remain active through the 500 ms crossfade. Stable scrollbar space avoids shifting the homepage, and reduced motion shows/closes immediately.

Validation: all 56 checks passed in Chromium viewport emulation (1440×960, 820×1180, 390×844, 412×915, 320×568 and 844×390). Checks cover first visit, refresh, new tab, original reset key, blocked storage and session fallback, Enter, close, Escape, Tab/Shift+Tab, focus restoration, background focus/scroll protection, delayed script loading, unchanged URL/document, crossfade geometry, reduced motion, bilingual layout, language preference, mobile drawer, contact dialog and a legacy bookmark. No runtime/resource errors or automated accessibility violations were found. This is viewport emulation, not physical-device or Safari verification.

A source comparison verifies that all original memorial words, homepage main/nav/footer markup and original inline scripts are unchanged. Other page files are unchanged, and the technical route loads without memorial assets. No additional overlay was created.
