"""Rich-powered CLI: menus, tables, prompts."""

from __future__ import annotations

import os
import sys

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt
from rich.table import Table

from tm.config import data_dir, paths
from tm.tasks import (
    add_task,
    archive_tasks,
    check_deadlines,
    delete_task,
    edit_task,
    export_to_csv,
    filter_due_today,
    filter_due_week,
    filter_overdue,
    get_task,
    import_from_csv,
    load_tasks,
    mark_done,
    parse_tags_line,
    stats_snapshot,
    task_matches_search,
    toggle_timer,
    view_tasks_sorted,
)
from tm.users import hash_password, load_user, save_user, setup_account_if_missing

console = Console()


def get_non_empty_input(prompt: str) -> str:
    while True:
        v = Prompt.ask(prompt, console=console).strip()
        if v:
            return v
        console.print("[red]Field required.[/red]")


def get_valid_date(prompt: str) -> str:
    from datetime import datetime

    while True:
        v = Prompt.ask(prompt, default="", console=console).strip()
        if not v:
            return "None"
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            console.print("[red]Use format YYYY-MM-DD[/red]")


def get_valid_priority() -> str:
    opts = {"1": "High", "2": "Medium", "3": "Low"}
    console.print("[cyan](1) High  (2) Medium  (3) Low[/cyan]")
    c = Prompt.ask("Priority", default="2", console=console).strip() or "2"
    return opts.get(c, "Medium")


def get_category() -> str:
    tasks = load_tasks()
    cats = list({t.get("category", "General") for t in tasks})
    console.print(f"[cyan]Existing categories: {', '.join(cats)}[/cyan]")
    v = Prompt.ask("Category", default="General", console=console).strip()
    return v or "General"


def get_recurrence(default_key: str = "0") -> str:
    console.print(
        "[cyan](0) none  (1) daily  (2) weekly  (3) monthly[/cyan]"
    )
    m = Prompt.ask("Recurrence", default=default_key, console=console).strip() or default_key
    return {"0": "none", "1": "daily", "2": "weekly", "3": "monthly"}.get(m, "none")


def recurrence_code(current: str) -> str:
    return {"none": "0", "daily": "1", "weekly": "2", "monthly": "3"}.get(
        (current or "none").lower(), "0"
    )


def display_task_table(tasks_list: list[dict], title: str = "Tasks") -> None:
    if not tasks_list:
        console.print(Panel("[yellow]No tasks match.[/yellow]", title=title))
        return
    table = Table(title=title, box=box.ROUNDED, show_lines=False)
    table.add_column("ID", style="bold", max_width=5)
    table.add_column("Cat", max_width=10)
    table.add_column("Description", max_width=28)
    table.add_column("Tags", max_width=14)
    table.add_column("Pri", max_width=8)
    table.add_column("Due", max_width=12)
    table.add_column("Rec", max_width=6)
    table.add_column("Blk", max_width=5)
    table.add_column("St", max_width=8)
    for t in tasks_list:
        tags = t.get("tags") or []
        if isinstance(tags, str):
            tags = [tags]
        tag_s = ", ".join(tags)[:14]
        desc = (t.get("description") or "")[:28]
        pri = t.get("priority", "Medium")
        pri_style = "bold red blink" if t.get("escalated") else (
            "red" if pri == "High" else "yellow" if pri == "Medium" else "cyan"
        )
        st = "[green]Done[/green]" if t["status"] else "[red]Open[/red]"
        dep = str(t.get("blocked_by") or "—")
        rec = (t.get("recurrence") or "none")[:6]
        table.add_row(
            str(t["id"]),
            (t.get("category") or "")[:10],
            desc,
            tag_s,
            f"[{pri_style}]{pri}[/]",
            str(t.get("due_date", "")),
            rec,
            dep,
            st,
        )
    console.print(table)


def show_main_menu() -> None:
    p = paths()
    console.print(
        Panel.fit(
            "[bold blue]TASK MANAGER[/bold blue]  ·  "
            f"data: [dim]{data_dir()}[/dim]\n"
            f"[dim]tasks → {os.path.basename(p['tasks'])}[/dim]",
            border_style="blue",
        )
    )
    console.print(
        "[bold]Tasks[/bold]     [cyan]1[/cyan] View all   [cyan]2[/cyan] Today & overdue   "
        "[cyan]3[/cyan] Next 7 days\n"
        "[bold]Create[/bold]    [cyan]4[/cyan] Add task   [cyan]5[/cyan] Edit   [cyan]6[/cyan] Detail\n"
        "[bold]Actions[/bold]   [cyan]7[/cyan] Search   [cyan]8[/cyan] Complete   [cyan]9[/cyan] Delete\n"
        "[bold]Organize[/bold] [cyan]10[/cyan] Sort   [cyan]11[/cyan] Timer   [cyan]12[/cyan] Stats\n"
        "[bold]Data[/bold]      [cyan]13[/cyan] Export CSV   [cyan]14[/cyan] Import CSV   [cyan]15[/cyan] Archive & exit"
    )


def login_interactive() -> bool:
    setup_account_if_missing(get_non_empty_input)
    user = load_user()
    for i in range(3, 0, -1):
        console.print(f"\n[bold]Login[/bold] ([cyan]{i}[/cyan] tries left). Type [cyan]forgot[/cyan] or [cyan]exit[/cyan].")
        u_input = Prompt.ask("Username", console=console).strip()
        if u_input.lower() == "exit":
            raise SystemExit(0)
        if u_input.lower() == "forgot":
            console.print(f"Question: {user['q']}")
            if hash_password(Prompt.ask("Answer", console=console).lower()) == user["a"]:
                user["password"] = hash_password(get_non_empty_input("New password: "))
                save_user(user)
                console.print("[green]Password reset.[/green]")
                continue
            console.print("[red]Answer does not match.[/red]")
            continue
        p_input = Prompt.ask("Password", password=True, console=console).strip()
        if u_input == user["username"] and hash_password(p_input) == user["password"]:
            console.print(f"[green]Access granted[/green] · Level [bold]{user.get('level', 1)}[/bold]")
            return True
    return False


def prompt_add_task() -> None:
    desc = get_non_empty_input("Description: ")
    pri = get_valid_priority()
    due = get_valid_date("Due date (YYYY-MM-DD or empty): ")
    cat = get_category()
    tags = parse_tags_line(Prompt.ask("Tags (comma-separated)", default="", console=console))
    notes = Prompt.ask("Notes (optional)", default="", console=console).strip()
    rec = get_recurrence("0")
    console.print("Blocked by another task? (ID or empty)")
    dep = Prompt.ask("Blocked by ID", default="", console=console).strip()
    blocked = int(dep) if dep.isdigit() else None
    add_task(desc, pri, due, cat, tags, notes=notes, recurrence=rec, blocked_by=blocked)
    console.print(f"[green]Task added under [{cat}].[/green]")


def prompt_edit_task() -> None:
    try:
        tid = IntPrompt.ask("Task ID", console=console)
    except (ValueError, KeyboardInterrupt):
        return
    t = get_task(tid)
    if not t:
        console.print("[red]Task not found.[/red]")
        return
    tg = t.get("tags") or []
    if isinstance(tg, list):
        tag_default = ", ".join(str(x) for x in tg)
    else:
        tag_default = str(tg)
    console.print(Panel(str(t), title=f"Task #{tid}", expand=False))
    console.print("[dim]Press Enter to keep current value.[/dim]")
    d = Prompt.ask("Description", default=t.get("description", ""), console=console)
    console.print("[cyan](1) High  (2) Med  (3) Low[/cyan]")
    inv = {"High": "1", "Medium": "2", "Low": "3"}
    pr = Prompt.ask(
        "Priority",
        default=inv.get(t.get("priority", "Medium"), "2"),
        console=console,
    ).strip()
    pmap = {"1": "High", "2": "Medium", "3": "Low"}
    pri = pmap.get(pr, t.get("priority", "Medium"))
    due = Prompt.ask(
        "Due YYYY-MM-DD",
        default="" if str(t.get("due_date") or "") in ("", "None") else str(t.get("due_date")),
        console=console,
    ).strip()
    cat = Prompt.ask("Category", default=t.get("category", "General"), console=console).strip()
    tags = Prompt.ask("Tags (comma-separated)", default=tag_default, console=console).strip()
    notes = Prompt.ask("Notes", default=t.get("notes") or "", console=console)
    rec = get_recurrence(recurrence_code(t.get("recurrence")))
    blk = Prompt.ask("Blocked by ID (empty=none)", default="", console=console).strip()
    updates: dict = {
        "description": d,
        "priority": pri,
        "category": cat,
        "tags": tags,
        "notes": notes,
        "recurrence": rec,
        "due_date": due if due else "None",
    }
    if blk == "":
        updates["blocked_by"] = None
    elif blk.isdigit():
        updates["blocked_by"] = int(blk)
    if edit_task(tid, updates):
        console.print("[green]Task updated.[/green]")
    else:
        console.print("[red]Update failed.[/red]")


def show_task_detail() -> None:
    try:
        tid = IntPrompt.ask("Task ID", console=console)
    except (ValueError, KeyboardInterrupt):
        return
    t = get_task(tid)
    if not t:
        console.print("[red]Not found.[/red]")
        return
    lines = []
    for k, v in sorted(t.items()):
        lines.append(f"[bold]{k}[/bold]: {v}")
    console.print(Panel("\n".join(lines), title=f"Task #{tid}", border_style="cyan"))


def prompt_search() -> None:
    q = Prompt.ask("Keyword, category, notes, or #tag", default="", console=console).strip().lower()
    display_task_table([t for t in load_tasks() if task_matches_search(t, q)], title="Search results")


def prompt_complete() -> None:
    raw = Prompt.ask("Task ID(s), comma-separated", console=console).strip()
    if not raw:
        return
    for part in raw.split(","):
        part = part.strip()
        if not part.isdigit():
            console.print(f"[red]Skip invalid: {part}[/red]")
            continue
        msg, info = mark_done(int(part))
        if msg.startswith("BLOCKED") or "not found" in msg.lower():
            console.print(f"[red]{msg}[/red]")
        elif "Already" in msg:
            console.print(f"[yellow]{msg}[/yellow]")
        else:
            console.print(f"[green]{msg}[/green]")
            if info:
                console.print(f"[gold]+{info['gain']} XP[/gold]")
                if info.get("leveled"):
                    console.print(f"[bold gold]Level up! Now level {info['new_level']}.[/bold gold]")


def prompt_delete() -> None:
    raw = Prompt.ask("Task ID(s) to delete", console=console).strip()
    if not raw:
        return
    for part in raw.split(","):
        part = part.strip()
        if not part.isdigit():
            continue
        if delete_task(int(part)):
            console.print(f"[green]Deleted #{part}[/green]")
        else:
            console.print(f"[red]No task #{part}[/red]")


def prompt_sort() -> None:
    s_map = {"1": "priority", "2": "due_date", "3": "category", "4": "id"}
    c = Prompt.ask("Sort: [1] priority [2] due [3] category [4] id", default="1", console=console).strip() or "1"
    display_task_table(view_tasks_sorted(s_map.get(c, "priority")), title="Sorted")


def prompt_timer() -> None:
    try:
        tid = IntPrompt.ask("Task ID", console=console)
    except (ValueError, KeyboardInterrupt):
        return
    r = toggle_timer(tid)
    if r:
        if "start" in r.lower():
            console.print(f"[green]{r}[/green]")
        else:
            console.print(f"[yellow]{r}[/yellow]")
    else:
        console.print("[red]Task not found.[/red]")


def show_stats() -> None:
    s = stats_snapshot()
    total = s["total"]
    done = s["done"]
    pct = int((done / total) * 20) if total else 0
    bar = "█" * pct + "░" * (20 - pct)
    console.print(
        Panel(
            f"Level [bold]{s['level']}[/bold]  ·  XP [bold]{s['xp']}[/bold]\n"
            f"Completed [bold]{done}[/bold] / [bold]{total}[/bold]\n"
            f"[green]{bar}[/green]",
            title="Player stats",
            border_style="blue",
        )
    )


def prompt_export() -> None:
    res = export_to_csv()
    if res == "No tasks to export.":
        console.print("[yellow]No tasks to export.[/yellow]")
    else:
        console.print(f"[green]Exported to {res}[/green]")


def prompt_import() -> None:
    default = paths()["export_csv"]
    p = Prompt.ask("CSV path", default=default, console=console).strip()
    n, err = import_from_csv(p)
    if err:
        console.print(f"[red]{err}[/red]")
    else:
        console.print(f"[green]Imported / merged {n} row(s).[/green]")


def run_main_loop() -> None:
    alerts = check_deadlines()
    for a in alerts:
        console.print(f"[red bold]{a}[/red bold]")
    running = True
    while running:
        show_main_menu()
        choice = Prompt.ask("Choose", console=console).strip()
        if choice == "1":
            display_task_table(load_tasks(), title="All tasks")
        elif choice == "2":
            tasks = load_tasks()
            today = filter_due_today(tasks)
            overdue = filter_overdue(tasks)
            merged = {t["id"]: t for t in overdue}
            for t in today:
                merged[t["id"]] = t
            display_task_table(list(merged.values()), title="Today & overdue")
        elif choice == "3":
            display_task_table(filter_due_week(load_tasks()), title="Due in 7 days")
        elif choice == "4":
            prompt_add_task()
        elif choice == "5":
            prompt_edit_task()
        elif choice == "6":
            show_task_detail()
        elif choice == "7":
            prompt_search()
        elif choice == "8":
            prompt_complete()
        elif choice == "9":
            prompt_delete()
        elif choice == "10":
            prompt_sort()
        elif choice == "11":
            prompt_timer()
        elif choice == "12":
            show_stats()
        elif choice == "13":
            prompt_export()
        elif choice == "14":
            prompt_import()
        elif choice == "15":
            n = archive_tasks()
            console.print(f"[green]Archived {n} completed task(s). Goodbye.[/green]")
            running = False
        else:
            console.print("[dim]Unknown option.[/dim]")


def run() -> None:
    try:
        if not login_interactive():
            console.print("[red]Locked out.[/red]")
            sys.exit(1)
        run_main_loop()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted.[/yellow]")
        sys.exit(0)


if __name__ == "__main__":
    run()
