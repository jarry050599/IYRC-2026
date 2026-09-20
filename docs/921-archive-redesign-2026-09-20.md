# LinkGuard — 921 Memory Edition

Implemented on 2026-09-20 against `cd393b47134ce43f1f7fdc59859c30fc5684b336`.

The brief is a modern research interface informed by the memory of the 1999 Chi-Chi earthquake: memory → reflection → engineering → technology → care. This is a presentation change across all 14 existing routes. Research content, measurements, limitations, application handlers and destination URLs are retained.

## Visual system

| Token | Value / use |
| --- | --- |
| Paper | `#F4F1EA`, primary page and navigation surface |
| Secondary surface | `#EAE6DE`, timeline, code, grouped context |
| Ink | `#1A1A1A`, titles and primary controls |
| Muted text | `#6B6258`, readable captions and metadata |
| Dark red | `#8A2E2E`, earthquake date/time, key metrics, selected navigation and interaction states |
| Muted gold | `#B59A6A`, fine rules and timeline markers |
| Typography | Apple-oriented system stack with Traditional Chinese system fallbacks; monospace for dates, coordinates, document labels and code |
| Spacing | Existing shared 8 / 12 / 16 / 24 / 32 / 48 / 64 / 80 / 96 / 120 px rhythm |
| Surfaces | Open sections and dividers; 6–12 px controlled radii; soft shadow only where separation is useful |
| Motion | 180 ms ease-out for UI states; reduced-motion overrides retained |

The final `archive-theme.css` layer covers both initial and expanded states, including legacy technical tables, firmware controls, comparison columns, dialogs, the mobile drawer and data diagrams. Existing image assets are unchanged. Documentary photographs receive a mild CSS saturation/sepia treatment; scientific figures, technical screenshots and certificate scans keep their original information.

## Page and component changes

- **Home:** a 1999.09.21 / 01:47 historical introduction, sourced Taiwan locator, past-to-future timeline, then the complete original LinkGuard introduction, evidence, system, team and award sections.
- **Navigation:** ARCHIVE, SYSTEM, RESEARCH and TECHNICAL collections retain all 13 page destinations. Current collection and current page remain explicit. Existing drawer, focus management, Escape and language behaviour remain intact.
- **Background:** THEN / 1999, WHAT WE LEARNED and NOW / 2026 frame the complete original research motivation, objectives, cases and references.
- **System:** emergency context precedes the modern architecture; a technology index leads to hardware disclosures. UWB links to the original planned-integration limitation, rather than implying an implemented capability.
- **Functionality:** the five-stage sensing-to-dispatch story and its selected-path highlighting use the restrained archive palette.
- **Data:** FIELD RECORD / SYSTEM DATA framing, large metrics, visible measurement/design/capacity labels and links to original basis tables.
- **Experiments:** FIELD REPORT 01–03, existing question/method/result/interpretation summaries, qualified results and full underlying research. Conditions repeat only source information; no experiment dates or precise field locations are invented.
- **Technical:** specification and protocol labels, readable code and firmware architecture, a spaced mobile outline and consistent tables/disclosures.
- **Comparison:** FIELD TECHNOLOGY REVIEW, restrained highlighted columns, sticky row labels and horizontal mobile scrolling.
- **Overview, development story, deployment, team, field records and awards:** shared archive typography, palette, captions, photo treatment and section rhythm. Cost/capacity estimates, original responsibilities, award records and real certificate assets remain intact.

## Historical and map provenance

No identifiable 1999 earthquake photographs were present in the project assets. No synthetic historical photograph, disaster scene, fault trace, seismogram or damage/intensity map was added.

- Historical event: [USGS event `usp0009eq0`](https://earthquake.usgs.gov/earthquakes/eventpage/usp0009eq0), verified against the [official GeoJSON feed](https://earthquake.usgs.gov/earthquakes/feed/v1.0/detail/usp0009eq0.geojson).
- The display uses Taiwan local date **1999-09-21**, time **01:47**, UTC+08:00. Seconds are intentionally not displayed.
- Locator: **23.772° N / 120.982° E**, explicitly labelled as the USGS catalog epicenter. It is a geographic reference, not an intensity map.
- Main-island outline: [Natural Earth 1:50m administrative geography](https://github.com/nvkelso/natural-earth-vector/blob/master/geojson/ne_50m_admin_0_countries.geojson), a public-domain dataset under its [terms of use](https://www.naturalearthdata.com/about/terms-of-use/). The SVG uses an equirectangular projection at 23.6° N.
- Source metadata is stored in `assets/archive/sources.json`. Both sources are linked visibly beside the locator.

Intermediate timeline stages are conceptual and undated. 2026 describes the contemporary project, not the date of an individual experiment.

## Preservation and verification

- All **3,398 original nonempty main-content text nodes** are retained across all 14 pages, after whitespace normalization.
- Every original anchor ID and link destination is retained.
- All original inline/external script tags are byte-identical. Application JavaScript files, APIs, backend, algorithms, research files and original media are unchanged.
- Service-worker changes are limited to the cache version and the two new presentation assets. Fetch/install/activation behaviour is unchanged. PWA background/theme colours now match the archive palette.
- Local asset/reference check: **0 missing local files**.
- Layout checks: all 14 routes at **1440 / 820 / 390 / 320 px**, with English overflow checks on mobile. **0 viewport overflow, 0 unexpected resource errors, 0 JavaScript runtime errors.**
- Original interaction regression: **28 checks passed**, covering keyboard skip link, mobile menu, focus trapping/restoration, language persistence, contact dialog, hardware disclosure, SOS diagram, flow selection, research and technical accordions, team details, photo lightbox, carousels, video-player insertion, table keyboard scrolling and legacy hash routing.
- Reading interactions: **20 checks passed**, including all home sections, cross-section disclosure, five-stage highlighting, full experiment details, pinned comparison labels, visible team responsibilities and real certificate loading.
- Theme/navigation checks: **32 checks passed**, including each route's retained destinations and current collection, UWB cross-page disclosure, historical CTA at desktop/mobile, English opening and drawer accessibility.
- Automated accessibility: **0 WCAG A/AA rule violations** in initial states on all 14 routes; **0** in expanded system, experiments, technical, story, team and awards views at desktop, 390 px and 320 px; **0** in the open mobile drawer. This is automated coverage plus targeted keyboard checks, not a claim of exhaustive accessibility certification.
- Offline reload and an offline second route retain the paper palette and required assets.
- Desktop/mobile screenshots were reviewed for the historical opening, timeline, system introduction, hardware specification, reports, metrics, workflow, tables, code, deployment, team, gallery and drawer.

The requested Apple Design Skill was not available in the environment after discovery. Implementation follows the user's supplied design requirements and uses no invented skill instructions.
