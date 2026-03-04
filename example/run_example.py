"""
run_example.py
--------------
快速体验示例脚本

直接运行：python examples/run_example.py
无需命令行参数。
"""

import asyncio
import sys
import os

# 确保能找到项目根目录的模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metagpt.team import Team
from metagpt.roles import Architect, Engineer, ProjectManager
from metagpt.roles.qa_engineer import QaEngineer
from rich.console import Console

from roles.persona_pm import PersonaPM
from roles.devil_advocate import DevilAdvocate

console = Console()

# ─── 示例需求（可以修改这里来体验不同场景）───
EXAMPLE_IDEA = "开发一个命令行版本的番茄钟工作法计时器，支持自定义工作时长和休息时长"


async def run_example():
    console.print("\n[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold cyan]")
    console.print("[bold cyan]  🍅 示例：番茄钟 CLI 工具开发[/bold cyan]")
    console.print("[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold cyan]\n")

    console.print(f"[green]需求：[/green]{EXAMPLE_IDEA}\n")

    console.print("[bold]本次示例将展示：[/bold]")
    console.print("  1. 🎭 PersonaPM 自动生成 3 个目标用户画像")
    console.print("  2. 📝 基于 Persona 生成 PRD 并进行对齐校验")
    console.print("  3. 😈 DevilAdvocate 对代码进行对抗性风险审查")
    console.print("  4. 🔍 QaEngineer 综合风险报告给出最终评审\n")

    team = Team()
    team.hire([
        PersonaPM(num_personas=3, validation_threshold=0.6),
        Architect(),
        ProjectManager(),
        Engineer(n_borg=3, use_code_review=False),
        DevilAdvocate(max_risks=4),
        QaEngineer(),
    ])

    team.invest(investment=3.0)
    team.run_project(EXAMPLE_IDEA)

    await team.run(n_round=5)

    console.print("\n[bold green]✅ 示例运行完成！[/bold green]")
    console.print("查看 ./workspace 目录获取生成的项目文件。\n")


if __name__ == "__main__":
    asyncio.run(run_example())
