"""
devil_advocate.py
-----------------
Role: DevilAdvocate（对抗性反驳智能体）

核心设计思想：
  在 Engineer 输出代码后、QAEngineer 正式 Review 前，
  插入一个"专门找茬"的 Agent。

  这个 Agent 的 Prompt 被硬性约束为：
    ✅ 只输出问题、风险、边界情况
    ❌ 不输出任何正面评价
    ❌ 不给出解决方案

  设计灵感：
    - 哈佛商学院"Devil's Advocate"决策技术
    - AI Safety 的 Red Teaming 方法
    - 避免 LLM "和事佬倾向"（总是先夸再轻描淡写提问题）

消息监听逻辑：
  - 监听 Engineer 的代码输出（WriteCode Action）
  - 输出风险报告，QAEngineer 同时收到代码和风险报告
"""

from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.logs import logger
from metagpt.actions.write_code import WriteCode

from actions.adversarial_review import AdversarialReview


class DevilAdvocate(Role):
    """
    对抗性反驳 Agent。
    
    在 Engineer → QA 的流程中插入，
    专门从反面视角审查代码，输出风险清单。
    """

    name: str = "Lucifer"
    profile: str = "DevilAdvocate"
    goal: str = (
        "从最严苛的角度审查工程师的代码和方案，"
        "找出所有潜在风险、边界情况和反例。"
        "只提问题，不给答案。"
    )
    constraints: str = (
        "严禁输出任何正面评价或解决建议。"
        "每条风险必须具体、可验证，不允许模糊表述。"
    )

    def __init__(self, max_risks: int = 5, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([AdversarialReview])
        # 监听 Engineer 的代码输出
        self._watch([WriteCode])
        self._max_risks = max_risks

    async def _act(self) -> Message:
        """
        DevilAdvocate 的执行逻辑：
          1. 获取 Engineer 输出的代码
          2. 调用 AdversarialReview 生成风险报告
          3. 发布风险报告（QAEngineer 会收到）
        """
        todo = self.rc.todo
        # 获取最近的代码消息
        memories = self.get_memories(k=1)
        if not memories:
            logger.warning("[DevilAdvocate] ⚠️ 未收到代码消息，跳过审查")
            return Message(content="未收到代码内容", role=self.profile)

        code_message = memories[0]
        code_content = code_message.content

        logger.info(
            f"[DevilAdvocate] 😈 {self.name} 开始对抗性审查，"
            f"代码长度：{len(code_content)} 字符"
        )

        # 执行对抗性审查
        adversarial_action = AdversarialReview(max_risks=self._max_risks)
        risk_report = await adversarial_action.run(code_content=code_content)

        output_message = Message(
            content=risk_report,
            role=self.profile,
            cause_by=type(todo),
        )

        logger.info("[DevilAdvocate] 😈 风险报告已发布，等待 QA Engineer 综合评审")
        return output_message
