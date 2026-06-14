# 数据 · 信用卡违约预测

- `UCI_Credit_Card.csv` —— UCI「default of credit card clients」，30,000 条 × 25 列（含 ID + 24 特征 + 标签）✅ 已纳入
- 标签列：`default.payment.next.month`（1 = 下月违约，0 = 不违约）；违约率约 22.1%

## 来源
- 官方：UCI Machine Learning Repository — default of credit card clients
- 本仓库取自 GitHub 公开镜像（Kaggle 整理版 `UCI_Credit_Card.csv`，列名规范）

## 字段速览
| 字段 | 含义 |
|------|------|
| LIMIT_BAL | 授信额度 |
| SEX / EDUCATION / MARRIAGE / AGE | 人口属性（⚠️ 用作特征涉公平/合规） |
| PAY_0 … PAY_6 | 近 6 个月还款状态（-1=按时，≥1=逾期月数） |
| BILL_AMT1 … 6 | 近 6 个月账单金额 |
| PAY_AMT1 … 6 | 近 6 个月还款金额 |
| default.payment.next.month | **标签**：下月是否违约 |
