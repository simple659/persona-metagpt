"""
persona_pm.py
-------------
Role: PersonaPM（带用户画像校验的产品经理智能体）

与原版 MetaGPT ProductManager 的区别：
  原版：直接接收需求 → 生成 PRD
  本版：接收需求 → 生成 Persona → 写 PRD → 校验每条需求与 Persona 的对齐度

这使得 PRD 不再是需求的简单堆砌，而是有用户价值支撑的产品文档。
"""

from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.logs import logger

from actions.generate_personas import GeneratePersonas
from actions.validate_prd import ValidatePRDWithPersonas


class PersonaPM(Role):
    """
    Persona 驱动的产品经理 Agent。
    
    工作流：
      1. 接收用户的一句话需求
      2. 调用 GeneratePersonas 生成目标用户画像
      3. 调用 ValidatePRDWithPersonas 生成并校验 PRD
      4. 输出带对齐报告的完整 PRD
    """

    name: str = "Alex"
    profile: str = "PersonaPM"
    goal: str = (
        "基于用户画像驱动的产品思维，生成有用户价值支撑的 PRD，"
        "并自动校验每条需求与真实用户诉求的对齐程度。"
    )
    constraints: str = (
        "PRD 中每条功能需求必须能对应至少一个用户画像，"
        "置信度不足的需求需要明确标注警告。"
    )

    def __init__(self, num_personas: int = 3, validation_threshold: float = 0.6, **kwargs):
        super().__init__(**kwargs)
        self._generate_personas = GeneratePersonas(num_personas=num_personas)
        self._validate_prd = ValidatePRDWithPersonas(
            validation_threshold=validation_threshold
        )
        # 注册 Actions
        self.set_actions([GeneratePersonas, ValidatePRDWithPersonas])
        self._watch(["metagpt.actions.add_requirement.AddRequirement"])

        # 暂存 Persona 数据，供后续 Action 使用
        self._personas: dict = {}

    async def _act(self) -> Message:
        """
        PersonaPM 的核心执行逻辑：
          Step 1: 生成 Persona
          Step 2: 生成 + 校验 PRD
        """
        # 从记忆中取最新消息
        todo = self.rc.todo
        msg = self.get_memories(k=1)[0]
        requirement = msg.content

        logger.info(f"[PersonaPM] 👤 {self.name} 开始处理需求：{requirement[:60]}...")

        # Step 1: 生成用户画像
        logger.info("[PersonaPM] Step 1/2：生成用户画像")
        self._personas = await self._generate_personas.run(requirement=requirement)

        # Step 2: 生成并校验 PRD
        logger.info("[PersonaPM] Step 2/2：生成并校验 PRD")
        validated_prd = await self._validate_prd.run(
            requirement=requirement,
            personas=self._personas,
        )

        # 将结果封装为 Message 发布到团队消息总线
        output_message = Message(
            content=validated_prd,
            role=self.profile,
            cause_by=type(todo),
        )

        logger.info("[PersonaPM] ✅ PersonaPM 任务完成，PRD 已发布")
        return output_message
