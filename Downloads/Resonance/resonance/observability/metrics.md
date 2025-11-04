# Resonance Metrics

All metrics are namespaced `resonance_` and follow Prom/OTEL conventions.

## Gauges

- `resonance_R` — Global coherence R(t) in [0,1]. Labels: `{service, instance}`
- `resonance_spectral_entropy` — Normalized spectral entropy in [0,1]. Labels: `{service, instance}`
- `resonance_coupling_K` — Current coupling strength K(t). Labels: `{service, instance}`
- `resonance_pll_bandwidth` — PLL bandwidth β. Labels: `{service, instance}`
- `resonance_controller_mode` — 0=observe,1=shadow,2=active,3=adaptive. Labels: `{service, instance}`
- `resonance_state` — Encoded state flags (bitfield). Labels: `{service, instance}`

## Histograms (HdrHistogram)

- `resonance_latency_p95` — p95 latency in ms. Labels: `{service, instance}`
- `resonance_latency_p99` — p99 latency in ms. Labels: `{service, instance}`
- `resonance_latency_p99_9` — p99.9 latency in ms. Labels: `{service, instance}`
- `resonance_latency_p99_99` — p99.99 latency in ms. Labels: `{service, instance}`
- `resonance_action_microdelay_ms` — Applied micro delay. Labels: `{service, instance, task_class}`
- `resonance_action_batch_size` — Applied batch size. Labels: `{service, instance, channel}`

## Counters

- `resonance_actions_total` — Total controller actions. Labels: `{service, instance, kind}`
  - `kind ∈ {microdelay, batch, dither, adjustK, bypass, hedge, retry}`
- `resonance_guard_trips_total` — Safety guard activations. Labels: `{service, instance, guard}`
  - `guard ∈ {anti_herd, anti_freeze, kill_switch}`
- `resonance_decisions_total` — Total decisions taken. Labels: `{service, instance, decision}`
  - `decision ∈ {execute, defer, batch, hedge}`
- `resonance_hedge_won_total` — Hedge wins. Labels: `{service, instance}`
- `resonance_hedge_fired_total` — Hedges fired. Labels: `{service, instance}`
- `resonance_retry_exhausted_total` — Retry failures. Labels: `{service, instance}`

## Latency (per route/queue)

- `latency_ms_p50|p95|p99|p99_9|p99_99` — Percentiles per route/queue. Labels: `{service, route}`
- `queue_depth` — Current depth per channel. Labels: `{service, channel}`

## Pairwise (sampled)

- `resonance_plv` — Pairwise phase‑locking value. Labels: `{service, i, j}` (use sparse top‑N only)

