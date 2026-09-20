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
- Entrance uses opacity only and completes in 1,500 ms. Exit fades over 500 ms, with a 600 ms event fallback.
- The close icon, Enter LinkGuard button and Escape all dismiss without navigation or reload.
- Closing records `linkguard-921-intro` in localStorage. sessionStorage is used when localStorage is inaccessible. If both are unavailable, the introduction still closes normally.
- Native modal background inertness, explicit focus containment, visible keyboard controls and focus restoration protect keyboard navigation. The dialog has a labelled title/description and `aria-modal="true"`.
- The existing language handlers serve the introduction's segmented control; no duplicate language state is introduced.
- Reduced motion removes entrance staging and closes immediately.
- Mobile uses `100dvh`, safe-area padding, 44 px language controls, a 48 px close control, and a 48 px minimum entry button. Short landscape screens can scroll the dialog content.
- The service-worker cache is updated to v28 to include the new presentation assets. Its install/fetch behavior is unchanged.

To see the introduction again, run the following in the browser console on LinkGuard and then reload:

```js
localStorage.removeItem('linkguard-921-intro');
```

## Validation

Baseline: commit `1e6c0440ddfcba23d18eed9b570e4af00506f02b`.

- All 3,594 original main-content text nodes across fourteen routes are retained. Existing IDs, links and image references are retained. Every original script block is preserved byte-for-byte.
- All fourteen routes checked at 1440, 820, 390 and 320 px (56 route/viewport combinations): no unintended horizontal overflow, missing resources, undersized text findings or page runtime errors. English checked on every mobile route.
- Forty-three memorial checks cover first visit, dismissal persistence, refresh, another tab, reset, close icon, Escape, focus containment/restoration, both languages, future-year calculation, storage failures, reduced motion, portrait/tablet/short landscape and unchanged URL/document.
- Original navigation, contact dialog, hardware disclosures, architecture simulation, functionality steps, experiment and technical accordions, story and team disclosures, photo lightbox, carousels, comparison keyboard scrolling and legacy bookmarks were exercised successfully.
- All six new operation links reach the original content and open specifications where applicable. The original system-overview bookmark still opens the retained node path.
- Fifty-seven referenced local image/PDF URLs return successfully; the proposal has a valid PDF signature. Existing unavailable certificate slots remain explicit placeholders.
- Automated WCAG A/AA checks report no violations on fourteen page views, the expanded research/technical/system/team views, the navigation drawer and the introduction in both languages. Keyboard checks complement the automated scan; this is not a claim of a formal accessibility certification.
- Desktop/mobile screenshots reviewed for all fourteen pages and detailed system, metric, technical, comparison, team and certificate sections.
- Offline home and technical route verified with the updated cache.

Validation uses Chromium desktop/mobile viewport emulation. Physical-device or Safari validation is not claimed.
