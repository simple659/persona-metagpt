# 设计文档 | Design Document

## 背景与动机

MetaGPT 是一个优秀的多智能体框架，但在实际使用中，我们观察到两个主要问题：

### 问题1：PRD 缺乏用户视角

原版 MetaGPT 的 ProductManager Agent 直接从"一句话需求"生成 PRD，
缺乏系统性的用户研究前置步骤。这导致生成的 PRD 往往是功能列表，
而非真正以用户价值为驱动的产品文档。

**解决方案**：引入 Persona-Driven PRD Validation 机制，
在写 PRD 之前先建立用户画像，再用画像反向校验每条需求。

### 问题2：Code Review 存在"和事佬效应"

LLM 在做 Code Review 时，有一种固有倾向：先给出正面评价，
再轻描淡写地提出一些问题。这种"和事佬倾向"会导致真正的风险被掩盖。

**解决方案**：引入 Devil's Advocate Agent，其 Prompt 被硬性约束为
"只输出问题，不输出正面评价，不给解决方案"。

---

## 技术设计

### Persona 生成与校验流程

```
需求输入
   │
   ├─→ GeneratePersonas Action
   │     输入：一句话需求
   │     输出：JSON 格式用户画像列表
   │
   └─→ ValidatePRDWithPersonas Action
         输入：需求 + Persona 列表
         步骤1：基于 Persona 生成 PRD
         步骤2：对每条需求做 Persona 匹配校验
         步骤3：生成对齐报告（含置信度 + 警告）
         输出：带校验标注的完整 PRD
```

### Devil's Advocate 插入位置

```
Engineer (WriteCode)
    │
    ├─→ [原版流程] QaEngineer 直接 Review
    │
    └─→ [改进流程]
         DevilAdvocate 监听 WriteCode 消息
              │
              ├─ 生成风险报告
              │
         QaEngineer 同时收到：
              ├─ 代码内容（来自 Engineer）
              └─ 风险报告（来自 DevilAdvocate）
              综合输出最终评审
```

### 消息流设计

```python
# DevilAdvocate 监听 Engineer 的代码输出
self._watch([WriteCode])

# QaEngineer 原本就监听多种消息类型，
# DevilAdvocate 的输出会自动进入其上下文
```

---

## 关键设计决策

### 为什么 Devil's Advocate 不给解决方案？

如果 Devil's Advocate 既找问题又给方案，它就变成了第二个 QA Agent，
两者会产生角色重叠。更重要的是，"找问题"和"给方案"是两种不同的认知模式：
强制 DA Agent 只做前者，保证了它的对抗性立场不会被"建设性思维"稀释。

### 为什么置信度阈值默认是 0.6？

0.6 是一个平衡点：过高（如 0.9）会导致大量误报，
过低（如 0.3）则形同虚设。0.6 意味着"超过一半的把握该需求服务某个用户"，
这是合理的"准入门槛"。

### Persona 数量为什么默认是 3？

用户研究领域的经验表明，2-4 个 Persona 足以覆盖大多数产品的核心用户群。
太多 Persona 会导致需求发散，太少则覆盖不足。3 是实践中的最优值。

---

## 已知局限性

1. **LLM 置信度的主观性**：Persona 匹配置信度由 LLM 自评，存在不一致性
2. **消息顺序依赖**：Devil's Advocate 依赖 MetaGPT 的消息总线顺序，
   在高并发场景下可能出现时序问题
3. **Persona 质量依赖 LLM**：生成的用户画像质量取决于 LLM 对产品领域的理解

## 未来改进方向

- [ ] 支持从真实用户访谈记录中提取 Persona
- [ ] Devil's Advocate 风险分类细化（目前依赖 LLM 自分类）
- [ ] 加入历史项目数据，让 Persona 校验更精准
- [ ] Web UI 展示 Persona 画像和风险报告
