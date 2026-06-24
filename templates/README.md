# LaTeX 论文模板（投稿件）

> 供 `modelcrew-writer` 的"LaTeX 输出模式"使用。Writer 先定稿 `6_paper.md`（内容真相源），
> 再据题型选模板、**只替换占位符内容、不动排版骨架**，生成 `cases/<题>/artifacts/6_paper.tex`。
> "内容 / 排版"解耦 ⟹ 换题复用时排版零改动。

## 两套模板
| 文件 | 赛制 | 引擎 | 说明 |
|---|---|---|---|
| `mcm_paper_template.tex` | 美赛 MCM/ICM | `pdflatex` / `latexmk -pdf` | 英文；Summary Sheet 单独成页；自包含标准宏包，无需 `mcmthesis.cls` |
| `cumcm_paper_template.tex` | 国赛 CUMCM | `xelatex` / `latexmk -xelatex` | 中文 `ctexart`；含承诺页占位；无需 `cumcmthesis.cls` |

> 两套均**自包含**：不假设本机装了官方赛题 `.cls`，用标准宏包保证能编译；文件头注释写了如何替换为官方模板。

## 占位符约定
Writer 把各节内容填进下列 `%%...%%` 占位符（**全部替换后** `.tex` 里不应再出现 `%%`）：

| 占位符 | 填什么 | 对应 6_paper.md 章节 |
|---|---|---|
| `%%TITLE%%` | 论文标题 | 标题 |
| `%%TEAM%%` | 队号/控制号（MCM）；国赛走承诺页 | — |
| `%%SUMMARY%%` | 摘要正文（最重要，单独打磨） | Abstract / 摘要 |
| `%%KEYWORDS%%` | 3–6 个关键词，逗号分隔 | — |
| `%%COMMITMENT%%` | 国赛诚信承诺书（按当年官方模板） | 仅 CUMCM |
| `%%SEC_RESTATE%%` | 问题重述（自己的话） | 1. Problem Restatement |
| `%%SEC_ASSUMPTIONS%%` | 假设清单（每条带理由） | 2. Assumptions |
| `%%SEC_NOTATION%%` | 符号说明表 | （从模型节提取） |
| `%%SEC_MODEL%%` | 模型建立（变量/方程/约束） | 4. Model Formulation |
| `%%SEC_SOLUTION%%` | 求解与结果（含图表解读） | 5. Results |
| `%%SEC_SENSITIVITY%%` | 灵敏度分析（MCM 独立大节） | 6. Sensitivity Analysis |
| `%%SEC_EVALUATION%%` | 模型评价：优点/局限/改进，**如实写入 Critic 的 ⚠️/❌** | 7. Model Evaluation |
| `%%SEC_CONCLUSION%%` | 结论 | 8. Conclusion |
| `%%REFERENCES%%` | `\bibitem{...} ...` 列表 | References |
| `%%APPENDIX%%` | 代码/补充材料 | Appendix |

## 铁律（与 Writer 一致）
- **数字唯一真相源** = `cases/<题>/artifacts/frozen_numbers.json`；`.tex` 与 `.md` 同源，**绝不在 LaTeX 里改出第二个版本的数字**。
- LaTeX 数学环境里用 `$...$`／`\[...\]` 重排 .md 里的公式；纯文本伪代码用 `verbatim`/`lstlisting`。
- 编译命令：
  ```bash
  # 美赛
  latexmk -pdf 6_paper.tex            # 或  pdflatex 6_paper.tex  (跑两遍出目录/引用)
  # 国赛（中文需 XeLaTeX）
  latexmk -xelatex 6_paper.tex
  ```
- 本机无 TeX 发行版时：交付 `.tex` 源，并在文档里**如实标注"未编译"**，不谎称已出 PDF。

## 可选：DOCX 输出（国赛/校内要 Word 时）
部分国赛赛道、校内赛或导师更习惯 Word。用 pandoc 从同源的 `.md` 直接生成可编辑 docx（公式走 LaTeX→OMML，**不是截图**）：
```bash
pandoc 6_paper.md -o 6_paper.docx        # 需本机装 pandoc
```
与 `.tex`/`.md` **同源同数字**——docx 只是另一种封装，不另造内容或数字。
