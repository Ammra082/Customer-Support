"""Workspace and member management tools."""

from sqlalchemy.orm import Session
from app.db.queries import get_workspace, log_action
from datetime import datetime


def check_workspace_usage(db: Session, user_id: str, **_) -> dict:
    ws = get_workspace(db, user_id)
    if not ws:
        return {"success": False, "error": "No workspace found."}
    used_pct = round((ws.storage_used_gb / ws.storage_limit_gb) * 100, 1) if ws.storage_limit_gb else 0
    result = {
        "success": True,
        "workspace_name": ws.name,
        "members": ws.member_count,
        "storage_used_gb": ws.storage_used_gb,
        "storage_limit_gb": ws.storage_limit_gb,
        "storage_used_pct": used_pct,
        "message": f"Using {ws.storage_used_gb} GB of {ws.storage_limit_gb} GB ({used_pct}%).",
    }
    log_action(db, "check_workspace_usage", user_id=user_id, result=result)
    return result


def invite_member(db: Session, user_id: str, member_name: str = "", member_email: str = "", **_) -> dict:
    ws = get_workspace(db, user_id)
    if not ws:
        return {"success": False, "error": "No workspace found."}
    name_label = member_name or member_email or "the specified user"
    ws.member_count += 1
    db.commit()
    result = {
        "success": True,
        "invited": name_label,
        "new_member_count": ws.member_count,
        "message": f"Invitation sent to {name_label}. They will receive a join link.",
    }
    log_action(db, "invite_member", user_id=user_id, parameters={"member": name_label}, result=result)
    return result


def reset_access(db: Session, user_id: str, target_user: str = "", **_) -> dict:
    label = target_user or "the specified user"
    result = {
        "success": True,
        "target_user": label,
        "message": f"Access credentials reset for {label}. They will receive a new login link.",
    }
    log_action(db, "reset_access", user_id=user_id, parameters={"target": label}, result=result)
    return result


def update_workspace_name(db: Session, user_id: str, new_name: str = "", **_) -> dict:
    ws = get_workspace(db, user_id)
    if not ws:
        return {"success": False, "error": "No workspace found."}
    if not new_name:
        return {"success": False, "error": "New workspace name is required."}
    old_name = ws.name
    ws.name = new_name
    db.commit()
    result = {
        "success": True,
        "old_name": old_name,
        "new_name": new_name,
        "message": f"Workspace renamed from '{old_name}' to '{new_name}'.",
    }
    log_action(db, "update_workspace_name", user_id=user_id, parameters={"new_name": new_name}, result=result)
    return result


def assign_role(db: Session, user_id: str, target_user: str = "", role: str = "member", **_) -> dict:
    label = target_user or "the specified user"
    result = {
        "success": True,
        "target_user": label,
        "role": role,
        "message": f"{label} has been assigned the role '{role}'.",
    }
    log_action(db, "assign_role", user_id=user_id, parameters={"target": label, "role": role}, result=result)
    return result


def export_workspace(db: Session, user_id: str, format: str = "csv", **_) -> dict:
    ws = get_workspace(db, user_id)
    name = ws.name if ws else "workspace"
    result = {
        "success": True,
        "format": format,
        "message": f"Export of '{name}' queued. You will receive a download link by email within 5 minutes.",
        "download_url": f"https://exports.taskflow.app/{user_id}/export.{format}",
    }
    log_action(db, "export_workspace", user_id=user_id, parameters={"format": format}, result=result)
    return result
