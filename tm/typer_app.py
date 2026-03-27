"""Typer entry: interactive menu, JSON batch, shell completion hooks."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated, Optional

import typer

from tm.batch import run_batch_json

app = typer.Typer(
    name="tm",
    help="Task Manager — interactive UI or JSON batch for scripting.",
    add_completion=True,
    pretty_exceptions_show_locals=False,
)


@app.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context) -> None:
    """With no subcommand, start the interactive Rich UI (login + menu)."""
    if ctx.invoked_subcommand is not None:
        return
    from tm.cli import run

    run()


@app.command("batch")
def batch_command(
    json_file: Annotated[
        Optional[Path],
        typer.Option(
            "--file",
            "-f",
            help="JSON file containing ops, or '-' for stdin",
        ),
    ] = None,
    stdin: Annotated[
        bool,
        typer.Option(
            "--stdin",
            "-s",
            help="Read JSON from stdin (same as -f -)",
        ),
    ] = False,
    compact: Annotated[
        bool,
        typer.Option("--compact", "-c", help="Single-line JSON output"),
    ] = False,
) -> None:
    """
    Run operations from JSON (for scripts and CI).

    \b
    Payload shape:
      { "ops": [ {"op": "list_tasks"}, {"op": "add_task", "description": "..."} ] }

    \b
    Or a bare JSON array: [ {"op": "stats"} ]

    \b
    Examples:
      tm batch -f ops.json
      echo '{"ops":[{"op":"list_tasks"}]}' | tm batch --stdin
      tm batch -f -
    """
    if json_file is None and not stdin:
        typer.echo("Error: provide --file PATH or --stdin (or -f -).", err=True)
        raise typer.Exit(2)

    if stdin and json_file is not None:
        typer.echo("Error: use either --stdin or --file, not both.", err=True)
        raise typer.Exit(2)

    try:
        if stdin or (json_file is not None and str(json_file) == "-"):
            text = sys.stdin.read()
        elif json_file is not None:
            text = json_file.read_text(encoding="utf-8")
        else:
            typer.echo("Error: no input.", err=True)
            raise typer.Exit(2)
    except OSError as e:
        typer.echo(f"Error reading input: {e}", err=True)
        raise typer.Exit(1) from e

    try:
        result = run_batch_json(text)
    except json.JSONDecodeError as e:
        typer.echo(f"Invalid JSON: {e}", err=True)
        raise typer.Exit(1) from e

    if compact:
        typer.echo(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    else:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))

    if not result.get("ok", False):
        raise typer.Exit(1)


@app.command("completion")
def completion_command(
    shell: Annotated[
        str,
        typer.Option("--shell", help="bash, zsh, fish, or powershell"),
    ] = "bash",
) -> None:
    """
    Print how to enable tab completion (Typer / Click).

    Prefer the built-in installer (works for bash, zsh, fish, PowerShell):

      python -m tm --install-completion

    argcomplete is for argparse-based CLIs; this app uses Typer, so use
    --install-completion or Click's completion env vars (see Click docs).
    """
    typer.echo(
        "Enable tab completion:\n\n"
        "  python -m tm --install-completion\n\n"
        "Or, from a checkout:\n\n"
        "  python task_manager.py --install-completion\n\n"
        f"(Ignored: --shell {shell} — the installer auto-detects your shell.)\n"
    )
