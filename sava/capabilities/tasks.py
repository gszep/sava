"""Google Tasks capabilities (read-only access to primary user's tasks)."""

from googleapiclient.discovery import build

from ..auth import get_primary_credentials


def _service():
    return build("tasks", "v1", credentials=get_primary_credentials())


def list_task_lists() -> str:
    service = _service()
    result = service.tasklists().list(maxResults=100).execute()
    items = result.get("items", [])
    if not items:
        return "No task lists found."

    lines = []
    for tl in items:
        lines.append(f"- **{tl['title']}**  \n  ID: `{tl['id']}`")
    return "\n".join(lines)


def list_tasks(tasklist_id: str = "@default", show_completed: bool = False) -> str:
    service = _service()
    result = (
        service.tasks()
        .list(tasklist=tasklist_id, showCompleted=show_completed, maxResults=100)
        .execute()
    )
    items = result.get("items", [])
    if not items:
        return "No tasks found."

    lines = []
    for task in items:
        status = "\u2705" if task.get("status") == "completed" else "\u2b1c"
        title = task.get("title", "(untitled)")
        parts = [f"{status} **{title}**"]
        if task.get("notes"):
            parts.append(f"  Notes: {task['notes'][:200]}")
        if task.get("due"):
            parts.append(f"  Due: {task['due']}")
        parts.append(f"  ID: `{task['id']}`")
        lines.append("\n".join(parts))

    return "\n".join(lines)
