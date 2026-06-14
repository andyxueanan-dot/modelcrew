# Data Brief — UCI 信用卡违约数据集

## Dataset Overview

- Source: UCI "default of credit card clients" (Yeh & Lien, 2009)
- Records: 30,000 rows × 25 columns (24 features + 1 target)
- Time span: April–September 2005 (Taiwan)
- Format: CSV, client-level records
- Target: `default.payment.next.month` (0=not default, 1=default)

## Field Documentation

### Identity & Credit Limit
| Field | Type | Range | Notes |
|-------|------|-------|-------|
| ID | int | 1–30,000 | Client identifier; **must be excluded from features** |
| LIMIT_BAL | float | 10,000–1,000,000 TWD | Credit limit; mean=167,484; right-skewed |

### Demographics (⚠️ SENSITIVE ATTRIBUTES)
| Field | Type | Range | Encoding | Notes |
|-------|------|-------|----------|-------|
| SEX | int | {1, 2} | 1=male, 2=female | ⚠️ Protected attribute; 60.4% female |
| EDUCATION | int | {0,1,2,3,4,5,6} | 1=graduate, 2=university, 3=high school, 4/5/6=others, 0=unknown | ⚠️ Protected; **0,4,5,6 undocumented** |
| MARRIAGE | int | {0,1,2,3} | 1=married, 2=single, 3=others, 0=unknown | ⚠️ Protected; **0 undocumented** |
| AGE | int | 21–79 | Mean=35.5 | ⚠️ Protected attribute |

### Payment History (KEY FEATURES)
| Field | Type | Range | Encoding | Notes |
|-------|------|-------|----------|-------|
| PAY_0 | int | {−2,−1,0,1..8} | −1=on time, −2=no consumption, 0=revolving, 1–8=months delayed | **Strongest predictor** (r=0.325); recent month |
| PAY_2..PAY_6 | int | same | same as PAY_0 | Historical months; correlation decreases with age |

### Bill Amounts
| Field | Type | Range | Notes |
|-------|------|-------|-------|
| BILL_AMT1..6 | float | −339,603 to 1,664,089 TWD | Negative = overpayment/credit; mean decreases over time |

### Payment Amounts
| Field | Type | Range | Notes |
|-------|------|-------|-------|
| PAY_AMT1..6 | float | 0 to 1,684,259 TWD | Actual payment; PAY_AMT2 max=1,684,259 (possible outlier) |

### Target
| Field | Type | Distribution | Notes |
|-------|------|-------------|-------|
| default.payment.next.month | int | 0: 23,364 (77.9%), 1: 6,636 (22.1%) | **Class imbalance: 3.5:1 ratio** |

## Quality Diagnostics

### Missing Values
**Zero missing values across all 25 columns.** Dataset is complete — no imputation needed.

### Outliers
- **PAY_AMT2 max = 1,684,259** vs mean = 5,921 (>280× mean). Likely a bulk payment or data entry error. Kept as-is (log transform may help).
- **BILL_AMT3 max = 1,664,089** vs mean = 47,013 (>35× mean). Extreme but plausible for high-limit clients.
- **LIMIT_BAL max = 1,000,000** — 68× the minimum. Long right tail.

### Inconsistencies
- **EDUCATION**: Values 0, 4, 5, 6 are undocumented. Combined = 468 records (1.6%). **Decision: Recode 0,4,5,6 as "Other/Unknown" (category 4).**
- **MARRIAGE**: Value 0 undocumented (54 records). **Decision: Recode 0 as "Other" (category 3).**
- **PAY_0..6 = 8**: Documented as "delayed 8+ months". Rare but valid.

### Target Imbalance
- Default rate: 22.1% (6,636 / 30,000)
- **Naive baseline** (predict all 0): accuracy = 77.9%
- Any useful model must beat 77.9% accuracy AND demonstrate discrimination on the minority class

## Cleaning Decision Log

| Step | Action | Rows Affected | Rationale |
|------|--------|--------------|-----------|
| 1 | Drop ID column from features | 0 | ID is an identifier, not a feature; including it risks data leakage |
| 2 | Recode EDUCATION 0,4,5,6 → 4 (Other) | 468 | Undocumented codes; grouping preserves information without noise |
| 3 | Recode MARRIAGE 0 → 3 (Other) | 54 | Undocumented code |
| 4 | No imputation | 0 | Zero missing values |
| 5 | No outlier removal | 0 | Extreme values are plausible for high-limit clients; log transforms preferred |

**Summary**: 30,000 → 30,000 rows (0 dropped); 3 columns recoded

## Derived Features (for modeling)

| Feature | Formula | Source | Justification |
|---------|---------|--------|--------------|
| pay_utilization | BILL_AMT_k / LIMIT_BAL | BILL_AMT + LIMIT_BAL | Credit utilization ratio; strong default signal |
| pay_delay_trend | PAY_0 − PAY_6 | PAY_0, PAY_6 | Deteriorating vs improving payment behavior |
| pay_ratio | PAY_AMT_k / BILL_AMT_k | PAY_AMT + BILL_AMT | Payment-to-bill ratio; low = struggling |
| total_debt | sum(BILL_AMT1..6) | BILL_AMT | Total debt burden |

## Data Traps

| Trap | Description | Impact |
|------|------------|--------|
| **⚠️ 准确率陷阱** | 77.9% naive baseline; 80% accuracy ≈ useless | Must evaluate with AUC/KS/F1, not accuracy |
| **⚠️ PAY_0 时间锚点** | PAY_0 = "recent month" status. If it encodes information from the same period as the target, it's leakage | Could inflate model performance by 5–10% AUC |
| **⚠️ 敏感属性** | SEX/AGE/EDUCATION are protected under fair lending laws | Model may discriminate; legal liability in deployment |
| **概念漂移** | 2005 Taiwan data; 2024 deployment = different world | Model performance will degrade without retraining |
| **ID leakage** | If ID correlates with signup date or other latent variables | Must be excluded from features |
