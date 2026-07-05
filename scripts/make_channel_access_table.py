import json
from pathlib import Path


APP_DIR = Path(__file__).resolve().parent
SOURCE_PATH = APP_DIR / "role_channel_access_report.json"
REPORT_PATH = APP_DIR / "role_channel_access_table.md"


def cell(items):
    if not items:
        return "-"
    return "<br>".join(items)


def main():
    data = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    type_labels = {
        "management": "Role จัดการ",
        "member_hierarchy": "Role สมาชิก/ลำดับชั้น",
        "job_or_game_class": "Role อาชีพ/เกม",
        "bot_role": "Role บอท",
        "bot_account": "Bot account",
        "bot_account_or_managed": "Managed/Bot role",
        "other": "อื่น ๆ",
        "default": "@everyone",
    }
    order = [
        "management",
        "member_hierarchy",
        "job_or_game_class",
        "bot_role",
        "bot_account",
        "bot_account_or_managed",
        "other",
        "default",
    ]

    roles_by_type = {}
    for role in data["roles"]:
        roles_by_type.setdefault(role["type"], []).append(role)

    lines = [
        "# Channel Access Table",
        "",
        f"Server: `{data['guild']['name']}`",
        "",
        "รายการช่องด้านล่างเป็นตัวอย่าง/รายการที่ role นั้นเข้าถึงได้จากข้อมูล audit ล่าสุด",
        "",
    ]

    for role_type in order:
        roles = roles_by_type.get(role_type, [])
        if not roles:
            continue

        lines.extend(
            [
                f"## {type_labels.get(role_type, role_type)}",
                "",
                "| Role | เห็นช่องแชท | ส่งข้อความได้ | เข้าช่องเสียงได้ | พูดในช่องเสียงได้ |",
                "|---|---|---|---|---|",
            ]
        )

        for role in roles:
            lines.append(
                f"| `{role['role']}` | {cell(role.get('text_view_channels', role['text_view_sample']))} | "
                f"{cell(role.get('text_send_channels', role['text_send_sample']))} | "
                f"{cell(role.get('voice_connect_channels', role['voice_connect_sample']))} | "
                f"{cell(role.get('voice_speak_channels', role['voice_speak_sample']))} |"
            )
        lines.append("")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(REPORT_PATH)


if __name__ == "__main__":
    main()
