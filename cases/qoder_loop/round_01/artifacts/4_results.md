# R1 Solver Results

## Q1 Optimal Plan
| Plot | Area | Irrigation | Crop | Water | Fert | Yield | Profit |
|------|------|-----------|------|-------|------|-------|--------|
| 1 | 200mu | Drip | Corn | 50000m3 | 6000kg | 120000kg | 246000 |
| 2 | 150mu | Flood | Soybean | 33750m3 | 2250kg | 30000kg | 153000 |
| 3 | 100mu | Rain | Corn | 10000m3 | 3000kg | 60000kg | 123000 |
| **Total** | 450mu | | | **93750m3** | **11250kg** | **210000kg** | **522000** |

## Constraint Tightness
- Water: 93750/100000 (slack 6250, 6.25%)
- Fertilizer: 11250/12000 (slack 750, 6.25%)
- Grain: 210000/80000 (surplus 130000, 162.5%!)

## Q2: Water Shadow Price
- Target: 574200 yuan (+10%)
- Min extra water: 12000 m3
- Achieved: 574500 yuan at +12000 m3

## Q3: Cotton Price Drop 15→10
- Optimal plan **unchanged** (still corn/soybean/corn)
- Profit unchanged at 522000 (cotton not in optimal plan)

## Key Insight
Cotton has highest per-mu profit (1650 yuan) but is NOT selected because:
1. High water (350m3) and fertilizer (35kg) per mu
2. Not a grain crop → doesn't contribute to grain constraint
3. Only feasible on Plots 1 and 2 (soil requirement 0.65)

## Feasibility Stats
- 64 total assignments → 48 soil-feasible → 10 fully feasible
