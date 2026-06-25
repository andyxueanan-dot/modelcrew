# R2 Solver Results

## OLS: R2=0.9964, Adj-R2=0.9948, RMSE=9.50, CV-RMSE=12.91

## Standardized Coefficients (ALL non-significant!)
| Feature | Beta | t | p |
|---------|------|---|---|
| PopDensity | +43.66 | 1.11 | 0.286 |
| MetroDist | -13.03 | -1.67 | 0.118 |
| BikeLane | +7.06 | 0.35 | 0.732 |
| POI | +36.00 | 1.08 | 0.298 |
| OfficeRes | +30.91 | 2.04 | 0.062 |
| Temp | +2.74 | 0.77 | 0.458 |

## VIF (EXTREME multicollinearity)
PopDensity=340.6, POI=244.6, BikeLane=90.2, OfficeRes=50.8, MetroDist=13.5, Temp=2.8

## Semi-partial R2 (ALL near zero)
OfficeRes 0.11% > MetroDist 0.08% > PopDensity 0.03% > POI 0.03% > Temp 0.02% > BikeLane 0.00%

## Forward Stepwise
Step1: PopDensity (R2=0.994) → +OfficeRes(+0.001) → +MetroDist(+0.001)

## Anomalies
#19 (SR=+3.13), #14 (SR=+2.41, CD=1.47), #11 (CD=0.34)

## Key Insight
R2=0.996 but ZERO significant predictors — classic severe multicollinearity.
PopDensity alone explains 99.4% of variance (forward stepwise R2=0.994).
All urban features (PopDensity, POI, BikeLane, OfficeRes) are measuring the same latent construct.
