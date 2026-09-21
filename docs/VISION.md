# HeatAction SG: decision and build guide

Prepared for Glen Tan, 21 September 2026. This is a proposed project and implementation plan, not a completed or evaluated system.

## 1. Recommendation

Enter **B1 HeatGuard** with **HeatAction SG**, a heat-response planner for community coordinators. Its defining question is: **Given the teams we have available, which neighbourhoods should we prioritise in the next hour, and why?**

My recommendation is based on achievable technical depth, accessible observational targets, a concrete operational decision and a demonstrable social benefit. No evidence can establish a numerical probability of winning or predict the other entries. The opportunity is to present a complete, well-tested product with an unusually clear connection between data and action.

The primary user is a coordinator supervising several AAC or volunteer teams. A single AAC may have a fixed catchment and cannot redeploy across Singapore. The app therefore filters recommendations to the user's actual service boundaries. Older residents benefit through better-directed support. The prototype does not identify individual people needing help.

### Comparison of the nine choices

These are project-selection judgments, not official rankings or a claim that every alternative dataset has been exhaustively audited.

| Statement | Opportunity | Main two-week execution risk | My view |
|---|---|---|---|
| A1 SilverWatch | Meaningful outreach planning | Public demographic proxies do not label actual social isolation | Strong if framed as planning, difficult to validate as prediction |
| A2 DengueRadar | Clear forecasting story | Need a consistent local historical case series and leakage-safe labels | Attractive only after a successful history audit |
| A3 HealthPulse | Important service planning | Local demand labels and credible five-year projections may be unavailable | Too many assumptions for this sprint |
| B1 HeatGuard | Observable heat target, live data and community decisions | Spatial coverage, forecast skill and current demographic resolution | Recommended with the scope below |
| B2 FloodSense | Compelling live demonstration | Historical flood events, non-event labels and rare-event evaluation | High execution risk |
| B3 ZeroWaste | Coverage and infrastructure planning | National waste totals do not establish local intervention effects | Feasible analytics, weaker causal claims |
| C1 FlatFair | Relatively straightforward supervised modelling | Differentiation and useful social impact beyond another estimator | Best fallback for a small or less experienced team |
| C2 MoveEasy | Tangible accessibility decisions | Walking distance is not proof of step-free access or journey suitability | Strong alternative with verified routes |
| C3 KopilamAI | Distinctively Singaporean service access | Location data do not establish meal prices or stall-level food waste | Strong if scoped to access and closures |

The official guide prioritises social impact and technical execution at the final round. The selection above is my inference about how to demonstrate both within the time available. Source: [DAISI participant guide](https://daisi.online/guide).

## 2. Product scope and user journey

**Illustrative scenario, with no measured results implied:** A coordinator has three team slots for the next hour. They select a service area and enter the number of contacts each team could realistically attempt. HeatAction SG proposes an allocation. The coordinator inspects the weather evidence and demographic assumptions, changes the budget to two slots, reviews the revised plan, and exports the result.

Prefer phone-based check-ins, activity adjustments and preparation of approved support over sending volunteers on long outdoor routes during heat. Specific intervention procedures belong to the organisation. The prototype supports planning and does not issue emergency instructions.

### MVP screens

1. **Conditions and priorities.** A map with source observations, planning-area demographic context, current weather timestamps and one-hour forecasts. Separate the observed heat layer from the planning-priority layer. Use grey for unavailable data.
2. **Plan with available teams.** Service-area filter, team-slot budget, contact-capacity assumptions, ranked areas and allocation comparison. Allow a coordinator to exclude an area or lock an assignment with a recorded reason.
3. **Why this recommendation?** Show forecast heat, senior share, baseline population year, station distance or regional assignment, forecast interval where validated, and the exact planning weights.
4. **Evidence.** Model versus baseline results, source freshness, pipeline quality checks and a labelled historical replay. This is useful for judges and maintainers without cluttering the coordinator's main screen.

**Core scope:** two live sources, one demographic baseline, matching polygons, one forecast horizon, one allocation method, one export.

**Extension only:** verified cooling-site access, additional weather signals, programme rescheduling, a Genie explanation interface, or alternative forecast horizons. Do not start these until the core flow works.

## 3. Data register and what is actually verified

The following catalogue descriptions and demographic fields were reviewed. Live API execution, historical download completeness and Databricks outbound access have not been demonstrated in this planning exercise. Treat them as the first feasibility gate.

| Data | Verified information | Use and limitation |
|---|---|---|
| [NEA WBGT Observations](https://data.gov.sg/datasets/d_87884af1f85d702d4f74c6af13b4853d/view) | Catalogue lists 15-minute updates and coverage starting February 2025 | Forecast observed WBGT. Download API specification and verify actual station/region schema and retrievable dates before promising a training interval. |
| [NEA Rainfall across Singapore](https://data.gov.sg/datasets/d_6580738cdd7db79374ed3152159fbd69/view) | Station readings update every five minutes | Second incremental source. Use only readings available by the forecast issue time. Check interval meaning before aggregation. |
| [Census 2020 age/sex population by planning area and subzone](https://data.gov.sg/datasets/d_d95ae740c0f8961a0b10435836660ce0/view) | Actual area rows and age bands, based on Master Plan 2019 | Obtain 65+ population and share. This is a 2020 baseline even though the catalogue was refreshed in 2026. |
| [URA Master Plan 2019 Planning Area Boundary, No Sea](https://data.gov.sg/datasets/d_4765db0e87b9c86336792efe8a1f7a66/view) | Matching boundary edition is listed | Join to planning-area totals. If using subzones later, obtain matching subzone polygons rather than treating planning-area polygons as subzones. |
| [SingStat population by planning region, age and sex](https://data.gov.sg/datasets/d_3c4dc32382bdc23189428af2126dd188/view) | Includes 2025 regional age counts | Fresh regional context and consistency checks. Planning regions are coarser than planning areas. Do not spread their totals into local areas and call them observed counts. |
| [AIC AAC directory](https://www.aic.sg/care-services/active-ageing-centres) | Public directory and description of activities and befriending | Optional candidate locations only. Public listings do not establish cooling status, opening hours, spare capacity or permission to direct residents there. |

The verified Census age bands for Ang Mo Kio total 35,220 residents aged 65+ in 2020: 11,960 + 9,930 + 5,770 + 4,150 + 2,280 + 1,130. This provides a concrete historical scale example, not a 2026 population estimate or a claim that it is the highest-risk area.

### Traps to avoid

- The [HDB elderly and future elderly dataset](https://data.gov.sg/datasets/d_c24f6b8078ee721f7191906ca1b3a367/view) inspected here contains age/sex percentages for survey years 2013 and 2018. It has no block identifier. Do not advertise block-level elderly counts from it.
- The [annual SAC/AAC series](https://data.gov.sg/datasets/d_0f70d7095a527be4ea443a7e30597896/view) contains national counts and access totals. It is not a geocoded inventory of available seats.
- WBGT, ordinary wet-bulb temperature and air temperature are different measurements. Do not substitute one for another or apply WBGT thresholds to air temperature.
- The 2025 URA boundary edition does not automatically match a Census 2020 table. Preserve boundary version and validate any crosswalk.
- Population at home does not reveal who is outdoors, isolated, medically vulnerable or without air-conditioning. These are unavailable attributes, not labels to invent.

Before freezing the submission, check whether a newer SingStat planning-area age table can be downloaded with compatible geography. If available, use it. Otherwise retain the clearly dated Census baseline, show the limitation in the app, and assess ranking sensitivity to population changes. A current regional table cannot establish current neighbourhood rankings.

## 4. First 48 hours: make feasibility concrete

1. Create the final Databricks Free Edition workspace and confirm a notebook, SQL warehouse and a minimal App can run. Confirm how teammates can work and who owns the final demo. Do not share passwords.
2. Open the two weather catalogue pages and download their API specifications. Retrieve one current response and a small historical sample. Inspect the actual location keys, coordinates, timestamps, units, pagination and error responses.
3. Test the same requests from Databricks. Free Edition has outbound network restrictions. If a source is unavailable there, ask the mentor about supported access and use reproducible manual file uploads to a managed volume for development. Clearly label any replay. Do not claim a replay is live.
4. Retrieve several historical days across the advertised period. Audit completeness, station changes and how much usable WBGT history overlaps rainfall. Aim for 8-12 weeks initially and expand only if necessary for seasonal validation.
5. Download the demographic CSV and matching boundaries. Extract planning-area totals, sum the total-sex 65+ bands, and calculate senior share. Confirm joins for a few areas and compare aggregates within published rounding tolerances.
6. Load these into Delta and display one real observation alongside one demographic row in the app. This proves the entire deployment path before model work.
7. Choose three pilot planning areas based on usable observations, data joins and a plausible coordinator catchment. Selection is not a finding about which neighbourhoods are most at risk.

**Decision gate:** If the next-hour target cannot be assembled from adequate observed history, retain current-observation planning and collect prospective data. Present forecasting as exploratory, with the actual sample period. If even the core data/deployment path remains blocked after 48 hours, switch to C1 FlatFair before investing in elaborate design.

## 5. Databricks implementation

Use Python and SQL. Small CPU models and scheduled incremental jobs are sufficient. Avoid Kafka, GPU training and an always-running streaming cluster for this prototype.

### Tables

| Layer/table | Grain and contents |
|---|---|
| `bronze.weather_responses` | Source, request time, retrieved time, response payload, checksum and run ID |
| `bronze.population_source` | Original rows, census year, source URL and snapshot checksum |
| `bronze.boundary_source` | Source geometry, boundary edition and snapshot checksum |
| `silver.weather_observations` | Source, source location, observed time, update time, value, unit and quality flags |
| `silver.population_area` | Planning-area key, baseline year, residents, residents aged 65+ and senior share |
| `silver.area_weather_link` | Area, source location, mapping method, distance where meaningful and validity dates |
| `gold.forecasts` | Issue time, target time, source location, prediction, optional interval, model version and mode |
| `gold.area_priorities` | Area, weather link, score components, weights, quality and demographic vintage |
| `gold.plan_results` | Scenario ID, budget, eligibility constraints, assumptions, assignments and run provenance |
| `gold.evaluation` | Split definition, baseline/model metrics, decision comparisons and sample counts |

### Ingestion and quality

Schedule notebook tasks with Lakeflow Jobs. Preserve raw source responses, then transform into managed Delta tables under Unity Catalog. During an active demo window, poll on an appropriate interval such as 15 minutes, subject to quota. Backfill historical pages only once and checkpoint progress. Confirm scheduling support in the actual workspace.

Deduplicate weather on source, location and observation timestamp. Handle corrected readings using the latest available source update while preserving raw versions. Keep UTC storage and Asia/Singapore display consistent. Use bounded retries and respect API rate limits. Quarantine malformed records and retain a run log with fetched, accepted, rejected and updated row counts.

Distinguish missing values, suppressed values and genuine zeros. Do not turn unknown observations into zero heat or zero rain. Do not count both area-total rows and their constituent subzones. Do not add male/female counts to total-sex counts. Document demographic rounding and geographic mapping exceptions.

Unity Catalog should contain meaningful table descriptions and source/vintage fields. Show the lineage actually captured by executed jobs. Record any model-stage dependencies that are not automatically represented instead of implying that every Python operation appears in native lineage.

Use the SQL warehouse for compact queries. A Databricks App can query Gold outputs and perform a small scenario allocation in Python. Start with CSV exports. Avoid a separate model-serving endpoint when notebook scoring meets the refresh requirement. Keep scenario writeback within available app permissions, or export the scenario with its assumptions if writeback is unavailable.

Databricks documents serverless-only Free Edition, restricted outbound internet, fair-use quotas, one small SQL warehouse and Apps that stop after 24 hours. Test and restart the final app before judging. Source: [Databricks Free Edition limitations](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations).

## 6. Forecasting that can be evaluated honestly

**Target:** the published WBGT reading at source location s at time t + 60 minutes. The reading itself represents a preceding 15-minute average. Build an exact timestamp target rather than shifting four rows when observations have gaps.

Train at the spatial resolution supplied by the API. If it supplies regions, forecast regions. If it supplies stations, forecast stations. A planning-area overlay is a spatial proxy, not a newly measured block temperature. Show mapping method, source distance when applicable and missing coverage. Do not silently equate NEA weather regions with URA planning regions.

**Baselines:** persistence, where the next-hour forecast equals the latest observation, and a time-of-day seasonal baseline estimated from training data only. A same-time previous-day baseline is also easy to evaluate.

**Candidate model:** one gradient-boosted regressor on CPU. Start with WBGT lags, recent changes, time-of-day sine/cosine, station identity and rainfall observed up to the issue time. Add air temperature or humidity only after verifying incremental predictive value. No resident demographics are needed to predict meteorological WBGT.

**Splitting:** divide all stations on common chronological boundaries. Keep the latest block as an untouched test set and use rolling-origin validation on earlier blocks. At each boundary remove training examples whose target time enters the next split. Learn imputations and transformations on training data only. Include rainy and hot days and report results by source location. Report uncertainty across days because adjacent readings are correlated.

**Metrics:** WBGT MAE in degrees Celsius; high-heat precision and recall using the applicable published category threshold; missed high-heat periods; sample counts and missingness by location. Use current observed categories directly where supplied. Version forecast-category rules using the current [official heat advisory](https://www.weather.gov.sg/heat-stress/).

Track feature lists, data versions, splits and metrics in MLflow. If a model fails to improve on a baseline, use the baseline and report the comparison. A credible negative result is better than a misleading improvement from random train/test splits.

If displaying forecast intervals, calibrate them on validation residuals and evaluate their held-out coverage. Say explicitly that temporal dependence and distribution changes limit the guarantee. If the sample is insufficient, omit probabilistic language. Forecast uncertainty does not quantify the separate uncertainty in population age or neighbourhood microclimates.

## 7. Explainable planning and allocation

Separate three objects: the measured/forecast weather hazard, the demographic planning proxy, and the allocation decision. Do not train an ML model on labels you created from your own scoring formula and call that validation.

A simple initial planning score is:

`P_i = H_i * (0.5 * percentile(E_i) + 0.5 * percentile(E_i / N_i))`

Here `E_i` is the area's baseline count of residents aged 65+, `N_i` is its total residents, and `H_i` is a declared heat-severity weight for the forecast period. As an illustrative policy, use 0, 1 and 2 for low, moderate and high advisory categories. These are planning weights, not clinical risk coefficients or probabilities. When all areas have weight zero, show no extra heat-driven allocation and retain normal operations.

Fix the percentile reference population to the documented pilot or national cohort. Do not recalculate it silently when a user filters the map. Expose the two demographic weights and test alternative settings. Unknown data should produce an unresolved status, not a reassuring low score.

For the MVP, assign at most one extra team slot per area in the selected period. Rank eligible areas by `P_i * q_i`, where `q_i` is assumed feasible contact capacity, capped by the demographic baseline and any confirmed operational limit. Select up to the available slot budget, honour locked/excluded areas and record unmet priorities. This is simple enough to audit. It estimates allocation value under assumptions, not the number of residents actually contacted.

If a user validates a need for multiple slots per area, add diminishing returns and a per-area capacity ceiling. A small integer programme can then maximise the summed incremental allocation value subject to team budgets and service boundaries. Add a fairness constraint only with a clear operational rationale. Do not build routing unless reliable travel times and safe operating procedures are available.

Compare equal allocation, elderly-count-only ranking and heat-only ranking under identical budgets, eligible areas and capacity assumptions. Re-run across held-out times and alternate weights. Evaluate realised weather at the future target time, not only the score the optimiser was designed to maximise. Report the contact capacity directed toward areas subsequently experiencing high heat, distribution across the service area and unmet priority. This remains simulation evidence rather than proof of fewer illnesses.

## 8. Evidence of benefit

| Question | Evidence to collect | Honest interpretation |
|---|---|---|
| Can the system forecast? | Chronological MAE and high-heat recall versus baselines | Predictive skill for observed WBGT over the evaluated period |
| Does allocation improve? | Same-budget held-out scenario comparisons and sensitivity tests | Better performance on stated planning proxies |
| Can someone use it? | Timed tasks and corrections in 2-3 relevant user walkthroughs if feasible | Early usability evidence, with the sample size disclosed |
| Is it technically reliable? | Repeat ingestion without duplicates, missing-feed behaviour and reproducible score/plan | Prototype reliability under tested conditions |
| Did health improve? | A later prospective partner evaluation would be needed | No such claim in the hackathon |

Treat an initial goal such as a 10% reduction in forecast MAE relative to the stronger baseline as a **target**, never a fabricated result. Prioritise accurate reporting over reaching a chosen percentage. For user testing, compare planning tasks with and without the app, counterbalance task order where practical and record mistakes as well as completion time.

Interview a coordinator or experienced volunteer before coding the allocation. Ask how priorities are currently set, what one team can do in an hour, which boundaries cannot be crossed, what makes a recommendation unusable, and how they would respond when forecasts disagree with conditions on the ground. Seek feedback yourself or with explicit permission. No contact has been made as part of this task.

## 9. Step-by-step schedule

The official timeline lists the concept deadline as 6 October 2026 at 11:59 PM SGT, the mentored sprint as 12-26 October and Demo Day as 27 October. Source: [participant guide](https://daisi.online/guide).

### Before the idea deadline

| When | Work | Completion evidence |
|---|---|---|
| 21-23 Sep | Form a team, audit source access, deploy a tiny app | One real row travels from ingestion to an app output |
| 24 Sep | Attend the advertised training if feasible; clarify platform questions | Known owner, permissions and deployment path |
| 25-28 Sep | Interview a prospective user; retrieve a sample history | Written workflow and data availability audit |
| 29 Sep-2 Oct | Prove one forecast target and a basic allocation | Baseline metric and one reproducible scenario |
| 3-5 Oct | Finalise concept, members and architecture | PDF, complete registration details and working source links |
| 6 Oct | Submit early enough to handle portal problems | Submission receipt before 11:59 PM SGT |

Check the competition rules before counting any pre-sprint implementation toward the final entry. Round 1 needs a concept, so user research and data validation are the essential preparation.

### Two-week build sprint

| Date | Task | Definition of done |
|---|---|---|
| 12 Oct | Confirm mentor scope and data gate | Fixed pilot, forecast target and eligible service area |
| 13 Oct | Bronze ingestion for both sources | Source payloads, checkpoints and repeatable reruns |
| 14 Oct | Silver cleaning and demographic joins | Missingness report and matching geography |
| 15 Oct | Baseline forecasts | Chronological evaluation and frozen test block |
| 16 Oct | Candidate model and MLflow | Reproducible comparison, no leakage |
| 17 Oct | Priority formula and allocation | Budgets/eligibility respected on meaningful scenarios |
| 18 Oct | End-to-end deployed prototype | Coordinator completes the entire flow |
| 19 Oct | Explanations, exports and source age | Every recommendation can be traced |
| 20 Oct | User walkthroughs | Feedback on the actual working app |
| 21 Oct | Fix important usability issues | Re-test the tasks that failed |
| 22 Oct | Evaluate forecast and plan | Final metrics, caveats and sensitivity results |
| 23 Oct | Quota, missing-feed and replay preparation | Clear live/replay status and failure behaviour |
| 24 Oct | Record demo and draft final submission | Coherent three-minute video and accessible code |
| 25 Oct | Freeze features and rehearse | Full run within the time limit |
| 26 Oct | Submit by the organiser's actual final cutoff | Links checked, permissions verified and backup ready |
| 27 Oct | Demo Day | Fresh app start, populated tables and rehearsed handoffs |

The exact final-submission cutoff is not specified in the supplied material beyond being before Demo Day. Obtain it from organisers and move the submission step earlier if necessary.

### Team ownership

For four members: one owns ingestion/governance; one owns forecasting/evaluation; one owns app/deployment; one owns user research, allocation and pitch. All should understand the pipeline. For three members combine allocation with modelling and share user research. For one or two, use a basic dashboard plus a small planner, one model, three pilot areas, and omit Genie/cooling-site extensions.

## 10. A three-minute demonstration

| Time | What to show |
|---|---|
| 0:00-0:20 | Name the coordinator and the decision: three team slots, several areas, changing heat |
| 0:20-0:45 | Real source timestamps and the observed/forecast heat layer |
| 0:45-1:15 | Ranked areas, age-profile context and one recommendation explanation |
| 1:15-1:45 | Reduce the budget and show the allocation change, then export |
| 1:45-2:15 | One visible pipeline run and the model/baseline comparison |
| 2:15-2:40 | A measured usability finding and held-out allocation comparison, if obtained |
| 2:40-3:00 | State the remaining limitation and the next partner pilot |

Use an explicitly labelled historical replay if the demonstration day is cool. Prepare it in advance with the exact timestamp and source snapshot. Never invent a hot live reading or present simulated contact numbers as completed outreach.

The strongest moment is changing a constraint and showing a defensible plan update. Keep technical details available for questions, while the main narrative stays with the coordinator's task.

## 11. Likely judge questions

**Doesn't myENV already show heat stress?**

Yes. HeatAction uses official environmental evidence to support a different decision: allocating a coordinator's finite team capacity within their service area. The forecast, demographic context and reviewable plan should demonstrate incremental value in user testing. Do not claim that an agency lacks tools you have not investigated.

**Where is the AI?**

The supervised model predicts future observed WBGT and is evaluated against credible baselines. The demographic planning score is explicit policy logic. Allocation is optimisation. Keeping these separate makes the result auditable.

**How do you know these residents are at risk?**

We do not identify individual illness risk. The app combines an environmental hazard proxy with aggregate age profiles to support prioritisation. It shows the age of those profiles and the limits of spatial coverage.

**How do you know the plan helps?**

Initially we can test planning time, understandability and simulation outcomes under equal budgets. A partner pilot with observed service outcomes is needed before claiming health benefits or operational adoption.

**What if the ML model is worse?**

We deploy the strongest evaluated baseline. We retain the observed-conditions planner and explain what the experiment found. The operational product remains useful if a coordinator validates its workflow.

**Why Databricks?**

It gives the team one place to preserve source data, run transformations, track models and serve governed outputs. The evidence is the working pipeline and traceable recommendation, not the number of product names in the architecture.

**How would this scale?**

Refresh compatible demographic data, validate area-weather mappings, and run a limited partner pilot. Add real aggregate capacity and eligibility data with appropriate access controls. Production deployment would require a suitable paid environment, operating ownership and monitoring. Free Edition is the prototype environment.

## 12. Round 1 submission and three-slide text outline

The prepared one-page concept note covers the requested problem, solution, data and intended architecture. Team name is a suggestion. Add the full member list in registration: each name, institution, course, year and email.

**Format ambiguity to resolve:** the current guide says a one-page concept or a three-slide PDF is accepted, but a later paragraph says every team submits the same three-slide template. The safest submission path is to place the concept into the [official template](https://daisi.online/guide) and export three slides unless organisers explicitly confirm the one-page route. The requested one-page note remains useful as the concise project description.

### Slide 1: Problem and why it matters

- Proposed team: HeatAction SG. Statement: B1 HeatGuard.
- Community coordinators need to decide where limited outreach support should go during hot periods.
- Census 2020 recorded about 35,220 residents aged 65+ in Ang Mo Kio alone. State the year clearly.
- Our pilot will turn environmental observations and age profiles into an explained plan within actual service boundaries.

### Slide 2: Solution and data

- User enters team slots and contact-capacity assumptions, inspects ranked areas and exports a reviewed plan.
- Data: NEA WBGT and rainfall, SingStat age-by-area population and matching URA polygons.
- Difference: a capacity-constrained decision, visible assumptions and a forecast tested against real observations.
- Pilot: three planning areas with audited coverage. Older demographic data remain explicitly dated.

### Slide 3: Architecture and impact

- Lakeflow Jobs orchestrate ingestion and transformation into Bronze/Silver/Gold Delta tables under Unity Catalog.
- MLflow records the forecast comparison. SQL and a Databricks App serve the planner and CSV export.
- Evaluation: forecast MAE/high-heat recall, allocation comparisons under equal budgets, task completion time and data-quality checks.
- Sprint outcome: runnable two-source pipeline, one-hour forecast evaluation and a demonstrated plan update. No health-impact claim before a real pilot.

Before final submission, replace aspirations with measured results wherever possible, retain unsuccessful comparisons where they matter, and make every demo number traceable to a data snapshot or a clearly labelled assumption.
