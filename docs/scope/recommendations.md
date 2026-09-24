# Epic: Recommendations and What If

Evidence based recommendations and scenario analysis. These features sit on top of the analytics outputs and provide actionable intelligence.

---

## Slice 5: Recommendation engine and what if analysis

### 23. Evidence based recommendation engine · needs a decision

Generate recommendations using the flow: Observation → Evidence → Interpretation → Recommendation → Priority. Recommendations must not be hard coded conclusions; they must be derived from the analytics outputs. Cover three recommendation domains: menu optimization (reprice, promote, remove, reposition), customer targeting (re-engage at risk, reward high value, upsell opportunities), and operational (reduce wastage, adjust preparation, optimize inventory).

**Done when:** recommendations are generated from real analytics outputs following the five step flow; each recommendation cites its evidence and observation; recommendations are prioritized; the three domains (menu, customer, operational) are covered; recommendations are API accessible and renderable in dashboards; no hard coded conclusions.

- [ ] Design it (spec): `/architect evidence based recommendation engine`

### 24. What if scenario analysis · needs a decision

Interactive scenario builder allowing users to model the impact of changes before making them. Scenario types: price changes, discount changes, promotion frequency, item removal, preparation quantity adjustment, predicted demand shift, and wastage assumption changes. Scenario outputs must include (where applicable): revenue, contribution margin, demand, wastage, and profitability. Results must be clearly labeled as estimates.

**Done when:** users can create scenarios for all seven scenario types; outputs show the applicable impact metrics (revenue, margin, demand, wastage, profitability); results are clearly labeled as estimates with confidence context; scenarios can be saved and compared; the UI supports parameter adjustment with immediate feedback.

- [ ] Design it (spec): `/architect what if scenario analysis`
