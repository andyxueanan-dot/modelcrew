# 评分维度 rubrics

> 供 `modelcrew-critic`（按维度打分审计）与 `modelcrew-writer`（对标写作）。
> 来源：MCM/ICM 基于 COMAP 公开评审标准；CUMCM 基于组委会公布维度与评委复盘的公开共识。
> 用法：每个阶段产出后，Critic 按对应竞赛的维度逐项给 1–10 分 + 证据。

## CUMCM 国赛维度（权重）
| 维度 | 权重 | 关键检查项 |
|---|---|---|
| 摘要质量 | 30% | 5 段结构 / 量化结果 / 创新表述 / 字数约 600–900 |
| 模型建立 | 25% | 与问题契合 / 假设有支撑 / 数学严谨 / 变量命名规范 |
| 求解与结果 | 20% | 算法合理 / 代码可复现 / 结果可视化 / 有物理意义 |
| 写作呈现 | 15% | 章节完整 / 公式编号 / 图表清晰 / 语言流畅 |
| 创新性 | 10% | 模型变体命名 / 跨学科融合 / 方法组合 |

## MCM/ICM 美赛维度
| 维度 | 关键检查项 |
|---|---|
| Summary（1 页） | 250–350 词 / ≥3 个量化结果 / 有 takeaway / 单页 |
| Approach & Modeling | 方法有新意 / 假设有支撑 / 推导严谨 |
| Solution & Results | 算法清楚 / 可复现 / **sensitivity 是独立大节** |
| Communication | 写作清晰 / 图表 self-contained / 术语精确 |
| Letter（D/E/F 题） | 可操作建议 / 通俗语言 / 写明局限 |

## 阶段级打分卡（Critic 每阶段产出后用，5 维 ×1–10）
```json
{
  "stage": "<router|analyst|scout|modeler|solver|writer>",
  "scores": {
    "对题契合度": 0,
    "严谨性": 0,
    "可复现性": 0,
    "结果质量": 0,
    "表达清晰度": 0
  },
  "verdict": "pass | refine | block",
  "evidence": "每个低分项必须给具体证据",
  "fixes": ["可操作的修复项"]
}
```
- **pass**：进下一阶段
- **refine**：diff-only 精修，最多迭代 3 次
- **block**：高严重度，必须人工介入

> Critic 铁律延伸：打分必须带证据，禁止"感觉不错→全 8 分"的橡皮图章。
