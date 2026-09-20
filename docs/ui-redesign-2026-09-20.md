# LinkGuard UI redesign — 2026-09-20

## Scope

Presentation and accessibility updates across all 14 existing pages. API contracts, backend code, data models, algorithms, application scripts, URLs, link destinations, and existing content anchors are unchanged. The original inline scripts were compared byte-for-byte after extraction from the HTML. All original anchor destinations and non-style IDs are preserved.

The requested Apple Design Skill was not available in the connected skill catalog. Implementation follows the supplied design requirements and Apple's Human Interface Guidelines principles; it is not an Apple certification.

| Route | Presentation changes |
| --- | --- |
| `index.html` | Split hero, existing search-vehicle photograph, clearer CTA priority, horizontal metrics |
| `overview.html` | Clear introduction, readable report width, full-width research summary |
| `background.html` | Open narrative layout, restrained quotation treatment, grouped facts |
| `system.html` | Disclosure rows for the six system modules, consistent icon and specification styling |
| `functionality.html` | Simplified process layout, accessible diagram scrolling, clear selected step |
| `data.html` | Prominent range measurements, quieter chart surfaces, mobile stacked labels |
| `experiments.html` | Consistent metric hierarchy, readable chart legends and tables, accessible horizontal chart scrolling |
| `research.html` | Minimal research timeline with native disclosures |
| `comparison.html` | Clear column hierarchy and keyboard-scrollable comparison table |
| `field.html` | Unified photography, carousel controls, video and lightbox presentation |
| `technical.html` | Consistent accordion rows, technical tables and reading width |
| `deployment.html` | Open deployment columns, shared typography and restrained cost emphasis |
| `team.html` | Portrait-led member rows and accessible expandable biographies |
| `awards.html` | Restrained award grouping and carousel; introductory copy no longer exposes asset-upload instructions |

## Shared design system

`design-system.css` is the final, shared visual layer. Repeated inline layout rules were consolidated into `site-foundation.css`, `site-layout.css`, and `site-technical.css`; the existing `multipage.css` remains in use. Page-specific technical layout support loads only where needed. Existing `wayfinder-ui.css` is retained but no longer linked by the pages.

- Fonts: Apple system stack with PingFang TC, Noto Sans TC and Microsoft JhengHei fallbacks; monospaced technical values use the system monospace stack. No remote decorative font dependency.
- Typography: responsive hero titles, section and subsection headings, 16px body copy, 14px labels, 12px metadata, and tabular numeric emphasis.
- Colors: white, `#f5f5f7` surfaces, `#1d1d1f` primary text, `#515155` secondary text, `#68686d` metadata, and `#0066b5` action blue. Status and chart colors retain semantic distinction.
- Spacing: 4, 8, 12, 16, 24, 32, 48, and 64px scale; responsive section spacing and a 1120px maximum content width.
- Shape: 10, 16, and 24px radius tokens; very light surface shadows, with stronger elevation reserved for menus and dialogs.
- Controls: one primary action style, quiet secondary actions, shared disclosure controls, visible keyboard focus, and touch-sized navigation controls.
- Navigation: three native disclosure groups containing the original thirteen destinations, explicit active states, and a separate mobile menu layout.
- Motion: restrained control transitions; decorative motion removed; reduced-motion preference supported.
- Responsive layouts: single-column mobile reading, stacked metrics and cards, flexible tablet layouts, and contained scrolling for intrinsically wide data.

`ui-accessibility.js` adds menu Escape handling, focus cycling in existing dialogs, and inert closed disclosure content without replacing the original application handlers. HTML now has a main landmark, visible skip-link focus, consistent primary headings, and labelled keyboard-scrollable data regions.

`sw.js` changes only the cache version and asset list to include the extracted styles and accessibility support. The existing service-worker lifecycle and fetch logic are unchanged.

## Verification

- All 14 routes reviewed at 1440, 820, 390, and 320px: 56 layout combinations with no uncontained horizontal overflow or JavaScript runtime errors.
- All 14 routes checked in English at 390px; English navigation additionally checked at 900, 1024, and 1440px.
- Screenshots reviewed for desktop, tablet, mobile, expanded technical content, charts, mobile navigation, and the contact dialog.
- 26 interaction and keyboard checks passed: language switching/persistence, mobile menu, navigation disclosure, Escape/focus restoration, modal focus cycling, module disclosure, architecture simulation, process-step selection, accordions, timeline, team biographies, photo lightbox, field carousel, video player creation, award playback and navigation, table keyboard scrolling, and legacy fragment routing.
- axe-core WCAG 2 A/AA and WCAG 2.1 AA automated checks completed across all 14 pages; identified text-contrast issues were corrected and the three affected pages rechecked with zero violations. This is automated coverage, not a full accessibility certification.
- Local link/fragment integrity, original script equality, original anchor destination equality, JavaScript syntax, and Git whitespace checks passed.
- New offline cache verified: home and technical pages retain the new styles while offline.
- Tests ran in Chromium. Safari/iOS and physical device testing were not performed.

## Pre-existing missing assets

Seven certificate images referenced by `awards.html` are absent from the original repository. Their original URLs and error/fallback behavior remain intact; the site continues to show its existing certificate placeholders. The missing images still return 404. No replacement certificates or award evidence were fabricated.
