"""
validate_prd.py
---------------
Action: ValidatePRDWithPersonas

在 PM Agent 完成 PRD 草稿后，
对每条需求自动进行"Persona 对齐校验"：
  ✅ 找到对应 Persona → 标注服务对象
  ⚠️ 找不到对应 Persona → 触发警告，建议重新评估

这模拟了真实 PM 工作中"需求与用户价值对齐"的 review 环节。
"""

import json
import re
from metagpt.actions import Action
from metagpt.logs import logger


WRITE_PRD_PROMPT = """
你是一位资深产品经理。
根据以下产品需求，结合提供的用户画像，撰写一份完整的产品需求文档（PRD）。

## 用户需求
{requirement}

## 目标用户画像
{personas_text}

## PRD 输出格式
请输出以下章节：

### 1. 产品概述
（50字以内的产品定位描述）

### 2. 目标用户
（基于上方画像，描述核心用户群体）

### 3. 核心功能需求
（列出 4-6 条核心功能，每条格式：功能名称 - 功能描述）

### 4. 非功能性需求
（性能、安全、兼容性等，2-3 条）

### 5. 暂不支持的功能
（明确排除在本期范围外的功能）
"""

VALIDATE_PRD_PROMPT = """
你是一位严格的产品评审专家。
请对以下 PRD 中的每条"核心功能需求"进行用户画像对齐校验。

## 用户画像
{personas_json}

## PRD 核心功能需求
{requirements_section}

## 校验任务
对每条功能需求，判断：
1. 它服务于哪个 Persona（填写 Persona ID，如 P1、P2）？
2. 置信度（0.0~1.0，1.0表示完全匹配）？
3. 如果置信度 < 0.6，输出警告原因。

请严格以 JSON 格式输出：
{{
  "validations": [
    {{
      "requirement": "需求名称",
      "matched_persona": "P1",
      "confidence": 0.9,
      "reason": "该功能直接解决 P1 的核心痛点",
      "warning": null
    }},
    {{
      "requirement": "需求名称",
      "matched_persona": null,
      "confidence": 0.3,
      "reason": "未找到明确匹配的用户画像",
      "warning": "⚠️ 建议重新评估此需求，或补充对应 Persona"
    }}
  ],
  "overall_score": 0.85,
  "summary": "总体评估一句话"
}}
"""


class ValidatePRDWithPersonas(Action):
    """
    PRD 与用户画像对齐校验 Action。
    
    流程：
      1. 先基于 Persona 生成 PRD
      2. 再对每条需求做 Persona 匹配校验
      3. 输出带校验标注的完整 PRD
    """

    name: str = "ValidatePRDWithPersonas"
    validation_threshold: float = 0.6

    async def run(self, requirement: str, personas: dict) -> str:
        logger.info("[PersonaPM] 📝 正在生成 PRD...")

        personas_text = self._format_personas_for_prompt(personas)
        prd_prompt = WRITE_PRD_PROMPT.format(
            requirement=requirement,
            personas_text=personas_text,
        )
        prd_draft = await self._aask(prd_prompt)

        logger.info("[PersonaPM] 🔍 正在进行 Persona 对齐校验...")
        requirements_section = self._extract_requirements_section(prd_draft)
        validation_prompt = VALIDATE_PRD_PROMPT.format(
            personas_json=json.dumps(personas, ensure_ascii=False, indent=2),
            requirements_section=requirements_section,
        )
        validation_response = await self._aask(validation_prompt)
        validation_result = self._parse_validation(validation_response)

        final_prd = self._merge_prd_with_validation(prd_draft, validation_result)
        self._log_validation_summary(validation_result)

        return final_prd

    def _format_personas_for_prompt(self, personas: dict) -> str:
        lines = []
        for p in personas.get("personas", []):
            lines.append(
                f"[{p['id']}] {p['name']}（{p['age']}岁，{p['occupation']}）\n"
                f"  - 核心诉求：{p['core_need']}\n"
                f"  - 痛点：{p['pain_point']}\n"
                f"  - 技术水平：{p['tech_savviness']}"
            )
        return "\n\n".join(lines)

    def _extract_requirements_section(self, prd: str) -> str:
        """提取 PRD 中的核心功能需求章节"""
        match = re.search(r'###\s*3[\.\s]*核心功能需求([\s\S]*?)###\s*4', prd)
        if match:
            return match.group(1).strip()
        # 兜底：返回整个 PRD
        return prd

    def _parse_validation(self, response: str) -> dict:
        """解析校验结果 JSON"""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            match = re.search(r'\{[\s\S]*\}', response)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
        return {"validations": [], "overall_score": 0.5, "summary": "校验结果解析失败"}

    def _merge_prd_with_validation(self, prd: str, validation: dict) -> str:
        """将校验标注追加到 PRD 末尾"""
        lines = [prd, "\n\n---\n\n## 📊 Persona 对齐校验报告\n"]

        overall = validation.get("overall_score", 0)
        summary = validation.get("summary", "")
        lines.append(f"**总体对齐分数：{overall:.0%}**  |  {summary}\n")

        has_warnings = False
        for v in validation.get("validations", []):
            persona_tag = v.get("matched_persona") or "未匹配"
            confidence = v.get("confidence", 0)
            bar = "🟢" if confidence >= 0.8 else ("🟡" if confidence >= self.validation_threshold else "🔴")
            lines.append(
                f"- {bar} **{v['requirement']}**  "
                f"→ 服务用户：`{persona_tag}`  置信度：`{confidence:.0%}`"
            )
            if v.get("warning"):
                lines.append(f"  > {v['warning']}")
                has_warnings = True

        if has_warnings:
            lines.append(
                "\n> ⚠️ **存在低置信度需求，建议产品经理重新评估或补充对应用户画像后再进入开发阶段。**"
            )

        return "\n".join(lines)

    def _log_validation_summary(self, validation: dict):
        score = validation.get("overall_score", 0)
        warnings = sum(1 for v in validation.get("validations", []) if v.get("warning"))
        logger.info(
            f"[PersonaPM] ✅ PRD 校验完成 | 对齐分数：{score:.0%} | 警告需求数：{warnings}"
        )
        if warnings > 0:
            logger.warning(f"[PersonaPM] ⚠️ 有 {warnings} 条需求未找到对应用户画像，请关注！")
