#!/usr/bin/env python3
"""
J.A.R.V.I.S v2 - Interactive REPL Entry Point.

Unified orchestrator with multi-agent, multi-provider architecture.
Beautiful terminal interface powered by Rich library.

Usage:
    python run_jarvis_v2.py

Special Commands:
    help    - Show available commands
    tools   - Show registered agent tools
    status  - Show provider/system status
    clear   - Clear conversation memory
    exit    - Exit the program (also: quit, q)
"""

import logging
import os
import sys

# Pastikan core module bisa di-import dari direktori ini
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from core.orchestrator import Orchestrator

# Setup logging - hanya WARNING ke atas agar tidak spam terminal
logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s - %(name)s - %(message)s",
)

# Rich console untuk output yang cantik
console = Console()


def print_banner() -> None:
    """Display the J.A.R.V.I.S welcome banner."""
    banner_text = (
        "[bold cyan]J.A.R.V.I.S[/bold cyan] v2.0\n"
        "[dim]Just A Rather Very Intelligent System[/dim]\n\n"
        "[green]Multi-Agent[/green] | [blue]Multi-Provider[/blue] | "
        "[yellow]Self-Healing[/yellow]\n\n"
        "[dim]Type [bold]help[/bold] for commands, "
        "[bold]exit[/bold] to quit[/dim]"
    )
    console.print(Panel(
        banner_text,
        title="[bold white]Welcome[/bold white]",
        border_style="cyan",
        padding=(1, 2),
    ))


def print_help() -> None:
    """Display available commands."""
    table = Table(title="Available Commands", border_style="cyan")
    table.add_column("Command", style="bold green")
    table.add_column("Description")

    table.add_row("help", "Show this help message")
    table.add_row("tools", "Show available agent tools")
    table.add_row("status", "Show provider and system status")
    table.add_row("clear", "Clear conversation memory")
    table.add_row("exit / quit / q", "Exit J.A.R.V.I.S")

    console.print(table)
    console.print(
        "\n[dim]Just type your question or task normally to interact with J.A.R.V.I.S.[/dim]"
    )


def print_tools(orchestrator: Orchestrator) -> None:
    """Display registered tools for the coding agent."""
    # Buat temporary coder agent untuk menampilkan tools
    from core.agents.coder_agent import CoderAgent
    from core.providers.ollama_provider import OllamaProvider

    # Gunakan dummy provider hanya untuk menampilkan tool list
    dummy_provider = OllamaProvider()
    agent = CoderAgent(provider=dummy_provider, model="display-only")
    tool_names = agent.get_tool_names()

    table = Table(title="Registered Tools (Coder Agent)", border_style="green")
    table.add_column("Tool", style="bold yellow")
    table.add_column("Description")

    for name in tool_names:
        if name in agent._tools:
            _, schema = agent._tools[name]
            desc = schema["function"]["description"]
            table.add_row(name, desc)

    console.print(table)


def print_status(orchestrator: Orchestrator) -> None:
    """Display system and provider status."""
    # Refresh provider status
    orchestrator.refresh_providers()
    status = orchestrator.get_status()

    # Provider status table
    table = Table(title="System Status", border_style="blue")
    table.add_column("Component", style="bold")
    table.add_column("Status")
    table.add_column("Details")

    # Ollama
    ollama_info = status["providers"]["ollama"]
    ollama_status = (
        "[green]Available[/green]"
        if ollama_info["available"]
        else "[red]Unavailable[/red]"
    )
    ollama_details = "Models: {} / {}".format(
        ollama_info["model_small"], ollama_info["model_medium"]
    )
    table.add_row("Ollama (Local)", ollama_status, ollama_details)

    # Groq
    groq_info = status["providers"]["groq"]
    groq_status = (
        "[green]Available[/green]"
        if groq_info["available"]
        else "[red]Unavailable[/red]"
    )
    rate_info = groq_info.get("rate_limit", {})
    groq_details = "Model: {} | Requests: {}/{}".format(
        groq_info["model"],
        rate_info.get("requests_last_minute", 0),
        rate_info.get("max_requests_per_minute", 30),
    )
    table.add_row("Groq (Cloud)", groq_status, groq_details)

    # Memory
    mem_info = status["memory"]
    mem_details = "Messages: {} / {} | Summary: {}".format(
        mem_info["messages"],
        mem_info["max_messages"],
        "Yes" if mem_info["has_summary"] else "No",
    )
    table.add_row("Memory", "[green]Active[/green]", mem_details)

    console.print(table)

    # Warning jika tidak ada provider
    if not ollama_info["available"] and not groq_info["available"]:
        console.print(
            "\n[bold red]WARNING:[/bold red] No LLM providers available!\n"
            "[dim]- Start Ollama: [bold]ollama serve[/bold]\n"
            "- Or set GROQ_API_KEY in .env file[/dim]"
        )


def process_input(orchestrator: Orchestrator, user_input: str) -> None:
    """Process user input and display the response.

    Args:
        orchestrator: The Orchestrator instance.
        user_input: The user's input text.
    """
    # Tampilkan spinner saat processing
    with console.status("[cyan]Thinking...[/cyan]", spinner="dots"):
        result = orchestrator.process(user_input)

    # Metadata: provider dan model yang digunakan
    meta_text = "[dim][{provider}] {model} | {task_type} ({difficulty})[/dim]".format(
        provider=result["provider"],
        model=result["model"],
        task_type=result["task_type"],
        difficulty=result["difficulty"],
    )
    console.print(meta_text)

    # Response content - render sebagai Markdown jika memungkinkan
    response_text = result["response"]
    if response_text:
        try:
            md = Markdown(response_text)
            console.print(Panel(md, border_style="green", padding=(0, 1)))
        except Exception:
            # Fallback ke plain text jika Markdown parsing gagal
            console.print(Panel(response_text, border_style="green", padding=(0, 1)))
    else:
        console.print(
            "[yellow]No response received. Check provider status with 'status' command.[/yellow]"
        )


def main() -> None:
    """Main entry point - Interactive REPL loop."""
    # Load environment variables dari .env file
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    load_dotenv(env_path)

    # Tampilkan welcome banner
    print_banner()

    # Inisialisasi orchestrator
    try:
        orchestrator = Orchestrator()
    except Exception as e:
        console.print(
            "[bold red]Error initializing J.A.R.V.I.S:[/bold red] {}".format(str(e))
        )
        sys.exit(1)

    # REPL loop
    while True:
        try:
            # Prompt input
            console.print()  # Blank line sebelum prompt
            user_input = console.input("[bold cyan]You>[/bold cyan] ")
            user_input = user_input.strip()

            # Skip input kosong
            if not user_input:
                continue

            # Handle special commands (case-insensitive)
            command = user_input.lower()

            if command in ("exit", "quit", "q"):
                console.print(
                    "\n[cyan]Sampai jumpa! J.A.R.V.I.S signing off.[/cyan]\n"
                )
                break

            elif command == "help":
                print_help()
                continue

            elif command == "tools":
                print_tools(orchestrator)
                continue

            elif command == "status":
                print_status(orchestrator)
                continue

            elif command == "clear":
                orchestrator.clear_memory()
                console.print("[green]Conversation memory cleared.[/green]")
                continue

            # Normal input - process melalui orchestrator
            process_input(orchestrator, user_input)

        except KeyboardInterrupt:
            # Ctrl+C - graceful exit
            console.print(
                "\n\n[cyan]Interrupted. Sampai jumpa![/cyan]\n"
            )
            break

        except EOFError:
            # End of input (piped input habis)
            console.print(
                "\n[cyan]End of input. J.A.R.V.I.S signing off.[/cyan]\n"
            )
            break

        except Exception as e:
            # Unexpected error - tampilkan tapi jangan crash
            console.print(
                "[bold red]Error:[/bold red] {}".format(str(e))
            )
            console.print("[dim]Type 'help' for available commands.[/dim]")


if __name__ == "__main__":
    main()
