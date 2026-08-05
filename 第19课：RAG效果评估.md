# CaraBot Agent 智能知识库系统课程
## 第 19 课：RAG 效果评估

### 🎯 本节课目标
- 理解 Recall@k 指标的计算方法和业务含义
- 掌握 CaraBot 的 Evaluator 评估框架
- 学会分析 badcase 并定位根因
- 学习评估驱动的参数调优流程
- 学习时长：2 天
- 实践任务：评估 RAG 效果并分析 badcase

---

## 1. Recall@k：检索质量的标尺

### 1.1 定义

> Recall@k = 前 k 个检索结果中，命中了多少个"正确答案"

```python
Recall@k = |检索到的前k个文档 ∩ 相关文档| / |相关文档总数|

示例：
  查询："公司年假政策"
  正确答案：doc_A, doc_B（共 2 个相关文档）
  
  top-3 检索结果：[doc_A, doc_C, doc_D]
  Recall@3 = |{doc_A} ∩ {doc_A, doc_B}| / 2 = 1/2 = 0.5
  
  top-5 检索结果：[doc_A, doc_C, doc_B, doc_E, doc_F]  
  Recall@5 = |{doc_A, doc_B} ∩ {doc_A, doc_B}| / 2 = 2/2 = 1.0 ✅
```

### 1.2 常用的 k 值

| k 值 | 场景 | 期望 |
|------|------|------|
| Recall@1 | 精准问答 | > 0.7 |
| Recall@3 | 一般 RAG | > 0.8 |
| Recall@5 | 宽泛搜索 | > 0.9 |
| Recall@10 | 全面检索 | > 0.95 |

---

## 2. CaraBot 的 Evaluator 框架

### 2.1 数据结构

```python
@dataclass
class EvalQuery:
    """一条测试用例"""
    query: str                    # 查询文本
    relevant_doc_ids: list[str]   # 人工标注的相关文档 ID
    language: str = "unknown"     # 语言标签（用于分语言分析）

@dataclass
class EvalResult:
    """单条评测结果"""
    query: str
    language: str
    recall_at_k: dict[int, float]  # {1: 0.5, 3: 0.8, 5: 1.0, 10: 1.0}
    retrieved_doc_ids: list[str]   # 实际召回的文档 ID 列表
    is_badcase: bool               # Recall@5 < 0.5
```

### 2.2 核心评估逻辑

```python
class Evaluator:
    async def evaluate(self, test_queries, k_values=None, threshold=None):
        if k_values is None:
            k_values = [1, 3, 5, 10]

        results = []
        for eq in test_queries:
            result = await self._evaluate_one(eq, k_values, threshold)
            results.append(result)

        # ① 总体 Recall@k
        overall_recall = {}
        for k in k_values:
            scores = [r.recall_at_k.get(k, 0.0) for r in results]
            overall_recall[f"recall@{k}"] = sum(scores) / len(scores)

        # ② Badcase 分析（Recall@5 < 0.5）
        badcases = [{
            "query": r.query,
            "language": r.language,
            "recall_at_5": r.recall_at_k.get(5, 0.0),
            "retrieved_ids": r.retrieved_doc_ids[:5],
        } for r in results if r.recall_at_k.get(5, 0.0) < 0.5]

        # ③ 分语言分析
        per_language = self._compute_per_language(results, k_values)

        return {
            "total_queries": len(results),
            "overall_recall": overall_recall,
            "per_language": per_language,
            "badcases": badcases,
        }
```

### 2.3 单条评估

```python
async def _evaluate_one(self, eq: EvalQuery, k_values, threshold):
    # 执行搜索
    search_result = await self._search_service.search(
        query=eq.query, top_k=max(k_values), threshold=threshold,
    )

    # 取检索到的 document_id
    retrieved_ids = [r["document_id"] for r in search_result["results"]]
    relevant_set = set(eq.relevant_doc_ids)

    # 计算每个 k 的 Recall
    recall_at_k = {}
    for k in k_values:
        retrieved_at_k = set(retrieved_ids[:k])
        hits = len(retrieved_at_k & relevant_set)
        recall_at_k[k] = hits / len(relevant_set) if relevant_set else 0.0

    return EvalResult(
        query=eq.query,
        language=eq.language,
        recall_at_k=recall_at_k,
        retrieved_doc_ids=retrieved_ids,
        is_badcase=recall_at_k.get(5, 0.0) < 0.5,
    )
```

---

## 3. 评估驱动的调优流程

### 3.1 标准流程

```
① 准备测试集（50-200 条标注查询）
     │
     ▼
② 运行评估 → 得到 baseline Recall@5
     │
     ▼
③ 分析 badcase → 分类问题根因
     │
     ├── 嵌入质量问题 → 换模型 / 调 chunk_size
     ├── 分块不合理 → 调整 chunk_size / overlap
     ├── 阈值问题 → 降低 threshold
     └── 标注问题 → 修正标准答案
     │
     ▼
④ 调整参数 → 重新评估 → 对比改善幅度
     │
     ▼
⑤ 迭代 ③-④ 直到 Recall@5 达标
```

### 3.2 Badcase 分类

| 类型 | 症状 | 根因 | 解决方向 |
|------|------|------|---------|
| **切分破坏** | 检索到正确文档但分数低 | chunk 边界切断了关键句 | 增加 overlap |
| **语义漂移** | 检索到语义相关但不含答案的文档 | 嵌入模型分辨力不够 | 换更大的模型 |
| **阈值误杀** | 正确答案被召回但分数低于 threshold | threshold 过高 | 降低 threshold |
| **标注错误** | 所谓"正确答案"其实不包含答案 | 人工标注有误 | 修正标注 |

### 3.3 分语言分析

```python
@staticmethod
def _compute_per_language(results, k_values):
    by_lang = {}
    for r in results:
        by_lang.setdefault(r.language, []).append(r)

    per_language = {}
    for lang, lang_results in by_lang.items():
        lang_recall = {}
        for k in k_values:
            scores = [r.recall_at_k.get(k, 0.0) for r in lang_results]
            lang_recall[f"recall@{k}"] = sum(scores) / len(scores)
        per_language[lang] = {
            "query_count": len(lang_results),
            "recall": lang_recall,
        }
    return per_language
```

**价值**：发现"中文 Recall@5=0.95 但斯瓦希里语 Recall@5=0.52" → 多语言嵌入模型在该语言上表现差 → 考虑针对该语言做数据增强或微调。

---

## 4. 评估脚本（evaluate.py）

```bash
python scripts/evaluate.py \
  --test-file data/test_queries.json \
  --k-values 1,3,5,10 \
  --threshold 0.7 \
  --output results/eval_report.json
```

测试数据格式（JSON）：
```json
[
  {
    "query": "公司年假政策是什么？",
    "relevant_doc_ids": ["doc_001", "doc_002"],
    "language": "zh"
  },
  {
    "query": "What is the annual leave policy?",
    "relevant_doc_ids": ["doc_003"],
    "language": "en"
  }
]
```

---

## 5. 课后作业

1. **标注测试集**：为 CaraBot 的知识库准备 20 条测试查询，人工标注相关文档 ID
2. **运行评估**：用 Evaluator 在测试集上运行评估，得到 Recall@k 基线
3. **Badcase 分析**：找出所有 Recall@5 < 0.5 的 badcase，手工分析原因并分类
4. **调优实验**：针对 badcase 类型调整参数（threshold、top_k、chunk_size），对比改善幅度
5. **分语言评测**：准备中英文测试数据各 10 条，对比分语言 Recall 差异

---

## 📚 扩展阅读
- MTEB 评估框架：https://github.com/embeddings-benchmark/mteb
- RAGAS 评估框架：https://docs.ragas.io/
- LangSmith 评估：https://docs.smith.langchain.com/evaluation

---

**下节课预告**：第 20 课 - Agent 架构与 LangGraph 框架（ReAct 模式、StateGraph、图结构）
