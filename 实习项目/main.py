"""
main.py
-------
persona-metagpt 入口文件

用法：
  python main.py "开发一个待办事项管理应用"
  python main.py "开发一个待办事项管理应用" --n_round 5 --no-devil
  python main.py "开发一个待办事项管理应用" --investment 5.0
"""

import asyncio
import typer
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from metagpt.team import Team
from metagpt.roles import Architect, Engineer, ProjectManager
from metagpt.roles.qa_engineer import QaEngineer

from roles.persona_pm import PersonaPM
from roles.devil_advocate import DevilAdvocate

app = typer.Typer(help="Persona-Driven Multi-Agent System with Adversarial Review")
console = Console()


def print_banner():
    """打印项目启动横幅"""
    banner = Text()
    banner.append("🧠 Persona-Driven Multi-Agent System\n", style="bold cyan")
    banner.append("   with Adversarial Review\n", style="bold cyan")
    banner.append("\n   基于 MetaGPT 的改进版多智能体框架", style="dim")
    console.print(Panel(banner, border_style="cyan", padding=(1, 4)))


def print_team_info(enable_devil: bool, num_personas: int):
    """打印团队配置信息"""
    console.print("\n[bold]📋 当前团队配置：[/bold]")
    console.print(f"  🎭 PersonaPM（画像数量：{num_personas}）")
    console.print("  🏗️  Architect")
    console.print("  💻 Engineer")
    if enable_devil:
        console.print("  😈 DevilAdvocate  ← [yellow]新增：对抗性风险审查[/yellow]")
    console.print("  🔍 QaEngineer")
    console.print("  📋 ProjectManager")
    console.print()


@app.command()
def main(
    idea: str = typer.Argument(..., help="你的产品需求，一句话描述，例如：'开发一个待办事项管理应用'"),
    investment: float = typer.Option(3.0, "--investment", "-i", help="投资金额（控制 API 调用上限）"),
    n_round: int = typer.Option(5, "--n-round", "-n", help="协作轮数"),
    num_personas: int = typer.Option(3, "--personas", "-p", help="生成用户画像数量（2-4）"),
    validation_threshold: float = typer.Option(0.6, "--threshold", "-t", help="Persona 匹配置信度阈值"),
    enable_devil: bool = typer.Option(True, "--devil/--no-devil", help="是否启用 Devil's Advocate Agent"),
    max_risks: int = typer.Option(5, "--max-risks", help="Devil's Advocate 最多输出风险条数"),
):
    """
    启动 Persona-Driven 多智能体团队，完成软件开发任务。

    \b
    示例：
      python main.py "开发一个 Markdown 笔记应用"
      python main.py "开发一个天气查询 CLI 工具" --no-devil
      python main.py "开发一个用户登录系统" --personas 4 --threshold 0.7
    """
    print_banner()
    print_team_info(enable_devil, num_personas)

    console.print(f"[bold green]💡 需求：[/bold green]{idea}\n")

    asyncio.run(
        _run_team(
            idea=idea,
            investment=investment,
            n_round=n_round,
            num_personas=num_personas,
            validation_threshold=validation_threshold,
            enable_devil=enable_devil,
            max_risks=max_risks,
        )
    )


async def _run_team(
    idea: str,
    investment: float,
    n_round: int,
    num_personas: int,
    validation_threshold: float,
    enable_devil: bool,
    max_risks: int,
):
    """异步运行多智能体团队"""

    # 构建团队成员
    team_members = [
        PersonaPM(
            num_personas=num_personas,
            validation_threshold=validation_threshold,
        ),
        Architect(),
        ProjectManager(),
        Engineer(n_borg=5, use_code_review=False),
    ]

    if enable_devil:
        team_members.append(DevilAdvocate(max_risks=max_risks))

    team_members.append(QaEngineer())

    # 组建团队
    team = Team()
    team.hire(team_members)
    team.invest(investment=investment)
    team.run_project(idea)

    console.print("[bold cyan]🚀 团队启动，开始协作...[/bold cyan]\n")

    # 运行
    await team.run(n_round=n_round)

    console.print("\n[bold green]✅ 项目完成！输出文件保存在 ./workspace 目录[/bold green]")

    if enable_devil:
        console.print(
            "[dim]💡 提示：Devil's Advocate 的风险报告已整合进 QA Engineer 的评审结果中[/dim]"
        )


if __name__ == "__main__":
    app()
