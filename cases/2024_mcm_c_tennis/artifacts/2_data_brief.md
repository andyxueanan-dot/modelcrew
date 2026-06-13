# Data Brief — 2023 Wimbledon Featured Matches

## Dataset Overview

- Source: 2024 MCM Problem C, 2023 Wimbledon Gentlemen's Singles
- Records: 7284 rows × 46 columns
- Matches: 31 (second round onward)
- Time span: 2023 Wimbledon Championships
- Format: CSV, point-by-point records

## Field Documentation (Key Fields)

| Field | Type | Range | Missing | Notes |
|-------|------|-------|---------|-------|
| match_id | str | 31 unique | 0% | Match identifier (e.g., "2023-wimbledon-1301") |
| player1, player2 | str | 19/22 unique | 0% | Player names; P1 listed first in draw |
| elapsed_time | str | HH:MM:SS | 0% | Time from match start |
| set_no, game_no, point_no | int | 1-5, 1-13, 1-337 | 0% | Hierarchical match structure |
| p1_score, p2_score | str | 14/15 unique | 0% | Current game score (0/15/30/40/AD) |
| server | int | {1, 2} | 0% | Who served: 1=P1, 2=P2 |
| serve_no | int | {1, 2} | 0% | First or second serve |
| point_victor | int | {1, 2} | 0% | **Who won the point: 1=P1, 2=P2** |
| p1_ace, p2_ace | int | {0, 1} | 0% | Ace on this point |
| p1_winner, p2_winner | int | {0, 1} | 0% | Winner (clean shot) |
| p1_unf_err, p2_unf_err | int | {0, 1} | 0% | Unforced error |
| rally_count | int | 0-34 | 0% | Number of shots in rally |
| speed_mph | float | 72-141 | **10.3%** | Serve speed (missing for non-serve points?) |
| serve_width | str | 5 categories | 0.7% | Serve direction (B/T/BW/...) |
| serve_depth | str | {CTL, NCTL} | 0.7% | Serve depth |
| return_depth | str | {D, ND} | **18.0%** | Return depth (Deep / Not Deep) |
| p1_distance_run, p2_distance_run | float | 0-156m | 0% | Distance run on this point |

## Quality Diagnostics

### Missing Values
- **speed_mph**: 752 missing (10.3%) — appears to be serve-related; likely missing for return points or changeovers. **Decision: Keep as-is, use NaN as indicator.**
- **return_depth**: 1309 missing (18.0%) — substantial; may be missing for points without a return (aces, double faults). **Decision: Keep as-is; encode as "Unknown" category.**
- **serve_width/serve_depth**: 54 missing (0.7%) — negligible. **Decision: No action needed.**

### Outliers
- **rally_count = 0**: Exists for some points (likely aces/service winners where no rally occurred). Not an error.
- **distance_run up to 156m on a single point**: Extreme but plausible for very long rallies. Not removed.
- **Max streak = 13 consecutive points**: Notable but not impossible given server dominance (67.3% server win rate).

### Duplicates
- No exact row duplicates detected (each point is sequential within match).

### Inconsistencies
- **p1_score values include "AD"** (Advantage) — standard tennis scoring, no issue.
- **game_victor and set_victor** are 0 except at game/set boundaries — expected behavior.

## Cleaning Decision Log

| Step | Action | Rows Affected | Rationale |
|------|--------|--------------|-----------|
| 1 | No rows dropped | 0 | Dataset is clean; all missing values have logical explanations |
| 2 | NaN preserved for speed_mph, serve_width, serve_depth, return_depth | 2169 total | Missing values are informative (indicate non-serve points or aces) |

**Summary**: Started with 7284 rows → after cleaning: 7284 rows (0 dropped)

## Derived Features (for modeling)

| Feature | Formula / Logic | Source | Justification |
|---------|----------------|--------|--------------|
| p1_won_point | (point_victor == 1).astype(int) | point_victor | Binary target variable |
| server_is_p1 | (server == 1).astype(int) | server | Server advantage control |
| p1_win_rate_recent | EWMA of p1_won_point (α=0.1) | p1_won_point | Q1: momentum index |
| momentum_index | EWMA(p1_performance) - EWMA(p2_performance) | Multiple fields | Q1: core momentum measure |
| current_streak | Count consecutive same point_victor ending at current point | point_victor | Q2: streak analysis |
| streak_length | Length of current streak | point_victor | Q2/Q3: streak features |
| is_swing | Sign change in momentum_index derivative > threshold | momentum_index | Q3: swing detection target |

## Data Traps

| Trap | Description | Impact |
|------|------------|--------|
| **Server confound** | Server wins 67.3% of points. A "streak" of server points may just be a service game, not momentum. | Could inflate apparent momentum effects by ~3× |
| **Game boundaries** | Points within a game have the same server. Streaks that span games (server changes) are fundamentally different from within-game streaks. | Must analyze streaks separately by service game |
| **Selection bias** | "Featured matches" may be selected for drama/close scores | May overstate momentum swings vs typical matches |
| **Non-stationarity** | Players fatigue, adapt tactics across a 5-set match | Momentum model may confound fatigue with momentum |
| **Small sample** | Only 31 matches | Limited power for Q4 generalization claims |
