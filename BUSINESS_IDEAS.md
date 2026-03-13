## EconGame — Business Mode Ideas

This file collects concrete, actionable ideas for a "Business Mode" feature. Use these as seeds for routes, data models, UI, and balancing.

1) Core Concepts
- Player-run businesses with costs, revenue, staff, and upgrades.
- Revenue = base income + modifiers (reputation, upgrades, staff efficiency, market events).
- Businesses produce items/services on a timer (tick-based or cron-like hourly processing).

2) Business Types (examples)
- Retail Shop: sells goods, profit depends on stock/markup and foot traffic.
- Service Provider: fixed contracts, recurring revenue (e.g., cleaners, dev shops).
- Factory: converts raw materials into products; requires supply chain management.
- Restaurant/Cafe: per-customer revenue, quality/ingredients determine tips and return rate.
- Tech Startup: requires investment, higher variance returns, potential IPO mechanic.

3) Progression & Upgrades
- Leveling: businesses gain XP from profit; levels unlock upgrades and capacity.
- Upgrades: increase output, reduce costs, unlock new product lines, reduce timer.
- Staff: hire employees (AI workers) with wage vs. productivity tradeoffs.
- Automation: invest to reduce manual player actions (passive income).

4) Finance & Risk
- Startup costs, maintenance costs, loan/lease options (integrate existing loan APIs).
- Taxes and inspections (periodic events that cost money or impose fines).
- Random events: supply shortage, demand surge, local competition, vandalism.

5) Markets & Economy
- Local demand model per city/region; businesses compete for market share.
- Dynamic pricing and inflation adjustments over time.
- Player-driven marketplace: buy/sell raw materials and products between players.
- Businesses can issue equity: allow player businesses to create shares, list on the stock market, and pay dividends. Shares can be bought/sold by players, affect control of the business, and enable IPO mechanics for scaling or acquisition.


6) Multiplayer & Interaction
- Franchising: buy into other players' businesses for shared profit.
- Partnerships and mergers (contracts between players).
- Competitions/auctions for high-profile contracts or city licenses.

7) UI/UX Features
- Business dashboard: profit/loss, hourly projection, staff list, inventory, tasks.
- Quick actions: open/close business, restock, set prices, run sale events.
- Notifications for inspections, low stock, and major events.

8) Admin / Owner Tools
- Owner-only controls: spawn business templates, inject events, pause businesses.
- Analytics endpoints: aggregate revenue, top businesses, active regions.

9) Monetization (in-game, not real money)
- Cosmetic upgrades for storefronts, prestige titles, trophies.
- VIP contracts that raise revenue but require reputation.

10) Balancing & Metrics
- Track metrics: revenue per hour, ROI, churn rate, average order value.
- Build tuning tasks: simulate businesses with different parameters to find sweet spots.

11) Implementation Notes / Starting Tasks
- Define `Business` model (id, owner, type, level, cash_balance, inventory, staff[], status).
- Create API routes: `/api/businesses` (list/create), `/api/business/<id>` (manage), `/api/business/<id>/tick` (process), `/api/business/<id>/upgrade`.
- Hook into existing hourly processor to call business ticks.
- Add templates: `business_list.html`, `business_detail.html`, `business_dashboard.html`.

12) Example Small-Scope MVP
- Implement one business type (Retail Shop) with: startup cost, inventory, restock, sell action, base profit.
- Add dashboard and hourly processing; let players create 1 shop and grow it via upgrades.

---
If you want, I can: (a) scaffold the data model and APIs, (b) implement the Retail Shop MVP, or (c) draft UI mockups and templates. Which should I do next?
