"""
adversarial_review.py
---------------------
Action: AdversarialReview

Devil's Advocate Agent 的核心 Action。

核心设计原则：
  - Prompt 被强制设定为"只输出问题、边界情况和反例，不给解决方案"
  - 这避免了 LLM 的"和事佬倾向"（倾向于先夸再提问题）
  - 输出的风险报告会传递给 QAEngineer，使其 Review 更全面

灵感来源：
  - AI Safety 领域的 Red Teaming 方法
  - 团队决策中的 Devil's Advocate 技术（哈佛商学院管理学）
  - Self-consistency 思路：从反方视角独立验证
"""

import json
import re
from metagpt.actions import Action
from metagpt.logs import logger


ADVERSARIAL_REVIEW_PROMPT = """
你是一个严格的技术风险审查员，你的唯一职责是找出以下代码/方案中的问题。

【重要规则】
1. 只输出问题、风险和反例
2. 绝对不要给出解决方案或建议
3. 绝对不要说任何正面评价
4. 每条风险必须具体，不能模糊
5. 最多输出 {max_risks} 条风险，按严重程度从高到低排列

## 代码/方案内容
{code_content}

## 风险类型参考（从以下维度寻找问题）
- 边界情况（Edge Cases）：输入为空、超大、特殊字符时的行为
- 错误处理：异常是否被吞掉？错误信息是否有意义？
- 性能问题：时间复杂度？大数据量时的表现？
- 安全漏洞：SQL 注入？XSS？未授权访问？
- 并发问题：多线程/异步场景下是否安全？
- 可维护性：硬编码？魔法数字？缺少注释？
- 依赖风险：第三方库版本锁定？单点故障？

## 输出格式（严格 JSON）
{{
  "risks": [
    {{
      "id": "R1",
      "severity": "高/中/低",
      "category": "风险类型",
      "description": "具体描述这个问题是什么，会在什么情况下触发",
      "trigger_condition": "什么情况下会出现这个问题"
    }}
  ],
  "risk_count": {{
    "high": 高风险数量,
    "medium": 中风险数量,
    "low": 低风险数量
  }},
  "verdict": "一句话总结：这份代码/方案是否存在阻塞性风险"
}}
"""


class AdversarialReview(Action):
    """
    对抗性代码审查 Action。
    
    输入：Engineer 的代码输出
    输出：结构化风险报告（JSON + 可读格式）
    
    注意：此 Action 故意不输出解决方案，
    避免"和事佬效应"，让 QAEngineer 独立判断如何处理风险。
    """

    name: str = "AdversarialReview"
    max_risks: int = 5

    async def run(self, code_content: str) -> str:
        logger.info("[DevilAdvocate] 😈 开始对抗性审查，寻找潜在风险...")

        prompt = ADVERSARIAL_REVIEW_PROMPT.format(
            code_content=code_content,
            max_risks=self.max_risks,
        )

        response = await self._aask(prompt)
        risk_data = self._parse_risks(response)
        formatted_report = self._format_risk_report(risk_data)
        self._log_risk_summary(risk_data)

        return formatted_report

    def _parse_risks(self, response: str) -> dict:
        """解析风险 JSON，容错处理"""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            match = re.search(r'\{[\s\S]*\}', response)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass

        # 兜底
        logger.warning("[DevilAdvocate] ⚠️ 风险报告解析失败，返回原始文本")
        return {
            "risks": [{"id": "R1", "severity": "中", "category": "解析错误",
                       "description": response[:200], "trigger_condition": "未知"}],
            "risk_count": {"high": 0, "medium": 1, "low": 0},
            "verdict": "风险报告解析失败，请人工审查"
        }

    def _format_risk_report(self, risk_data: dict) -> str:
        """将风险数据格式化为可读的 Markdown 报告"""
        counts = risk_data.get("risk_count", {})
        verdict = risk_data.get("verdict", "")

        lines = [
            "## 😈 Devil's Advocate 风险报告",
            "",
            f"> **总结**：{verdict}",
            f"> 高风险：{counts.get('high', 0)} 条 | "
            f"中风险：{counts.get('medium', 0)} 条 | "
            f"低风险：{counts.get('low', 0)} 条",
            "",
        ]

        severity_emoji = {"高": "🔴", "中": "🟡", "低": "🟢"}

        for risk in risk_data.get("risks", []):
            emoji = severity_emoji.get(risk.get("severity", "低"), "⚪")
            lines.append(
                f"### {emoji} [{risk['id']}] {risk.get('category', '未知类型')} "
                f"（{risk.get('severity', '未知')}风险）"
            )
            lines.append(f"**问题描述**：{risk.get('description', '')}")
            lines.append(f"**触发条件**：{risk.get('trigger_condition', '')}")
            lines.append("")

        lines.append(
            "\n> ⚠️ **以上为 Devil's Advocate Agent 的单方面风险陈述，"
            "不代表最终结论。请 QA Engineer 综合正反意见后做出判断。**"
        )

        return "\n".join(lines)

    def _log_risk_summary(self, risk_data: dict):
        counts = risk_data.get("risk_count", {})
        high = counts.get("high", 0)
        medium = counts.get("medium", 0)
        low = counts.get("low", 0)
        total = high + medium + low

        logger.info(
            f"[DevilAdvocate] 😈 审查完成 | 共发现 {total} 条风险 "
            f"（高:{high} 中:{medium} 低:{low}）"
        )
        if high > 0:
            logger.warning(f"[DevilAdvocate] 🔴 存在 {high} 条高风险，建议重点关注！")
