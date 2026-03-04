"""
generate_personas.py
--------------------
Action: GeneratePersonas

在 PM Agent 写 PRD 之前，先根据用户的一句话需求，
自动生成 2-3 个目标用户画像（Persona）。

每个 Persona 包含：
  - 姓名（虚构）
  - 年龄 & 职业
  - 核心诉求（1-2 句话）
  - 痛点（使用现有方案时的问题）
  - 使用频率（高/中/低）

这些 Persona 会在后续 ValidatePRDWithPersonas 中被引用，
用于验证每条需求是否有真实用户支撑。
"""

import json
from metagpt.actions import Action
from metagpt.logs import logger


GENERATE_PERSONAS_PROMPT = """
你是一位资深用户研究专家。
根据以下产品需求，生成 {num_personas} 个典型目标用户画像（Persona）。

## 产品需求
{requirement}

## 输出要求
请严格以 JSON 格式输出，不要包含任何额外说明文字。格式如下：

{{
  "personas": [
    {{
      "id": "P1",
      "name": "画像姓名（虚构）",
      "age": 年龄数字,
      "occupation": "职业",
      "core_need": "核心诉求，1-2句话",
      "pain_point": "当前解决方案的痛点",
      "usage_frequency": "高/中/低",
      "tech_savviness": "技术熟练度：专家/中级/新手"
    }}
  ]
}}

注意：
1. Persona 要有明显差异（不同年龄段、不同使用场景）
2. 核心诉求要具体，不要模糊
3. 痛点要真实，基于真实用户行为
"""


class GeneratePersonas(Action):
    """
    生成目标用户画像 Action。
    
    输入：产品需求（一句话）
    输出：JSON 格式的用户画像列表
    """

    name: str = "GeneratePersonas"
    num_personas: int = 3

    async def run(self, requirement: str) -> dict:
        logger.info(f"[PersonaPM] 🎭 正在生成用户画像，需求：{requirement[:50]}...")

        prompt = GENERATE_PERSONAS_PROMPT.format(
            requirement=requirement,
            num_personas=self.num_personas,
        )

        response = await self._aask(prompt)

        # 解析 JSON，容错处理
        personas = self._parse_personas(response)

        # 美观打印
        self._log_personas(personas)

        return personas

    def _parse_personas(self, response: str) -> dict:
        """从 LLM 返回中提取 JSON，容错处理"""
        try:
            # 尝试直接解析
            return json.loads(response)
        except json.JSONDecodeError:
            # 尝试提取 JSON 块
            import re
            match = re.search(r'\{[\s\S]*\}', response)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass

        # 兜底：返回结构化错误信息
        logger.warning("[PersonaPM] ⚠️ Persona 解析失败，使用默认画像")
        return {
            "personas": [
                {
                    "id": "P1",
                    "name": "默认用户",
                    "age": 25,
                    "occupation": "互联网从业者",
                    "core_need": "高效完成核心任务",
                    "pain_point": "现有方案操作繁琐",
                    "usage_frequency": "高",
                    "tech_savviness": "中级",
                }
            ]
        }

    def _log_personas(self, personas: dict):
        """在控制台美观展示 Persona 信息"""
        logger.info("[PersonaPM] 🎭 用户画像生成完毕：")
        for p in personas.get("personas", []):
            logger.info(
                f"  [{p['id']}] {p['name']} | {p['age']}岁 | {p['occupation']} | "
                f"使用频率：{p['usage_frequency']} | 技术水平：{p['tech_savviness']}"
            )
            logger.info(f"       诉求：{p['core_need']}")
            logger.info(f"       痛点：{p['pain_point']}")
