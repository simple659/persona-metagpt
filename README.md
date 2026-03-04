[README.md](https://github.com/user-attachments/files/25735449/README.md)
# 🧠 Persona-Driven Multi-Agent System with Adversarial Review

> **基于 MetaGPT 的改进版多智能体框架** | A MetaGPT extension with Persona validation & Adversarial Review

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://python.org)
[![MetaGPT](https://img.shields.io/badge/Based%20on-MetaGPT-orange)](https://github.com/FoundationAgents/MetaGPT)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 📌 项目简介 | Overview

本项目在 [MetaGPT](https://github.com/FoundationAgents/MetaGPT) 的基础上，针对原有多智能体协作流程的两个关键痛点进行了改进：

1. **产品侧**：原版 PM Agent 直接生成 PRD，缺乏对"用户是谁"的系统性思考。本项目引入 **Persona 驱动的需求校验机制**，在生成 PRD 之前先构建用户画像，并验证每条需求是否有真实用户支撑。

2. **工程侧**：原版 Review Agent 仅做单向正向评价，容易产生"回音壁效应"。本项目引入 **Devil's Advocate Agent（反驳智能体）**，专门输出潜在风险与反例，让 Review 环节具备对抗性验证能力。

This project extends MetaGPT with two targeted improvements:
1. **Persona-Driven PRD Validation** — PM Agent builds user personas before writing PRD, then validates each requirement against them.
2. **Adversarial Review (Devil's Advocate)** — A dedicated agent that challenges engineer outputs with risks and counterexamples before the final review.

---

## 🏗️ 架构设计 | Architecture

```
User Input (one-line requirement)
        │
        ▼
┌─────────────────────┐
│   PersonaPM Agent   │  ← 新增：先生成 Persona，再写 PRD，最后校验每条需求
│  (产品经理 + 画像)    │
└────────┬────────────┘
         │  validated PRD
         ▼
┌─────────────────────┐
│   Architect Agent   │  ← 原版：系统设计
└────────┬────────────┘
         │  system design
         ▼
┌─────────────────────┐
│   Engineer Agent    │  ← 原版：代码实现
└────────┬────────────┘
         │  code output
         ▼
┌─────────────────────────┐
│  DevilAdvocate Agent    │  ← 新增：输出风险清单 & 反例
│  (反驳智能体)            │
└────────┬────────────────┘
         │  risk report
         ▼
┌─────────────────────┐
│   QAEngineer Agent  │  ← 原版：综合正反意见，最终 Review
└─────────────────────┘
```

---

## ✨ 核心改动说明 | Key Innovations

### 1. Persona-Driven PRD Validation（用户画像驱动的需求校验）

**问题**：传统 Agent 生成的 PRD 往往是需求堆砌，缺乏真实用户视角。

**改动**：
- `GeneratePersonas` Action：自动生成 2-3 个目标用户画像（年龄、职业、核心诉求、痛点）
- `ValidatePRDWithPersonas` Action：对 PRD 每条需求标注"服务哪个 Persona"，找不到对应 Persona 的需求会触发 ⚠️ 警告

**效果示例**：
```
需求：支持深色模式
→ 对应 Persona：Persona B（25岁程序员，夜间高频使用）✅

需求：提供企业级 SSO 登录
→ 对应 Persona：未找到匹配画像 ⚠️ 建议重新评估此需求
```

---

### 2. Devil's Advocate Agent（对抗性反驳智能体）

**问题**：MetaGPT 原版的 Code Review 是单向正向评估，容易遗漏潜在风险。

**改动**：
- 新增 `DevilAdvocate` Role，在 Engineer 和 QAEngineer 之间插入
- `AdversarialReview` Action：Prompt 被强制设定为"只输出问题、边界情况和反例，不给解决方案"
- QAEngineer 在收到代码的同时也收到风险报告，综合输出最终评审

**灵感来源**：该设计参考了 AI Alignment 领域的 *adversarial prompting* 思路，以及团队决策中的 "Red Team" 方法论。

---

## 🚀 快速开始 | Quick Start

### 环境安装

```bash
git clone https://github.com/YOUR_USERNAME/persona-metagpt.git
cd persona-metagpt

pip install -r requirements.txt
```

### 配置 API Key

```bash
cp config/config.yaml.example config/config.yaml
# 编辑 config.yaml，填入你的 LLM API Key
```

支持的模型（在 `config/config.yaml` 中切换）：
- OpenAI GPT-4 / GPT-3.5
- DeepSeek（国内推荐）
- 通义千问 Qwen

### 运行

```bash
# 基础运行
python main.py "开发一个待办事项管理应用"

# 指定投资轮数
python main.py "开发一个待办事项管理应用" --n_round 5

# 查看示例
python examples/run_example.py
```

---

## 📁 项目结构 | Project Structure

```
persona-metagpt/
├── main.py                        # 入口文件
├── requirements.txt
├── config/
│   └── config.yaml.example        # 配置模板
├── roles/
│   ├── __init__.py
│   ├── persona_pm.py              # 🆕 PersonaPM：带画像校验的产品经理 Agent
│   └── devil_advocate.py          # 🆕 DevilAdvocate：对抗性反驳 Agent
├── actions/
│   ├── __init__.py
│   ├── generate_personas.py       # 🆕 生成用户画像
│   ├── validate_prd.py            # 🆕 PRD 与 Persona 对齐校验
│   └── adversarial_review.py      # 🆕 对抗性代码审查
├── examples/
│   └── run_example.py             # 示例脚本
└── docs/
    └── design.md                  # 设计文档
```

---

## 📊 与原版 MetaGPT 对比 | Comparison

| 特性 | 原版 MetaGPT | 本项目 |
|------|-------------|--------|
| PRD 生成 | 直接生成 | Persona 校验后生成 |
| 需求合理性验证 | ❌ | ✅ 自动标注 + 警告 |
| Code Review 模式 | 单向正向 | 对抗性双向验证 |
| 风险识别 | 依赖 QA | 独立 Devil's Advocate |
| 国内模型支持 | 需配置 | 开箱即用 |

---

## 🤝 致谢 | Acknowledgements

本项目基于 [MetaGPT](https://github.com/FoundationAgents/MetaGPT) 开发，感谢原项目团队的出色工作。

MetaGPT paper: *MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework* (ICLR 2024 Oral, Top 1.2%)

---

## 📄 License

MIT License
