"""Excel 批量导入联系人。"""

from typing import Any

from openpyxl import load_workbook

from models import add_contact


def import_excel(file_path: str) -> dict[str, Any]:
    """从 Excel 文件导入联系人。

    支持的列格式（第一行为表头）：
        - 姓名 / name / 联系人
        - 电话 / phone / 电话号码 / 号码
        - 分组 / group（可选）

    Args:
        file_path: Excel 文件路径

    Returns:
        {"success": 成功数, "skipped": 跳过数, "errors": 错误列表}
    """
    wb = load_workbook(filename=file_path, read_only=True)
    ws = wb.active

    # 读取表头，匹配列索引
    headers = [str(cell.value).strip().lower() if cell.value else ""
               for cell in next(ws.iter_rows(min_row=1, max_row=1))]

    name_col = _find_column(headers, ["姓名", "name", "联系人"])
    phone_col = _find_column(headers, ["电话", "phone", "电话号码", "号码", "手机"])
    group_col = _find_column(headers, ["分组", "group", "类别"])

    if name_col is None or phone_col is None:
        wb.close()
        return {"success": 0, "skipped": 0,
                "errors": ["未找到姓名或电话列，请确保表头包含「姓名」和「电话」"]}

    result = {"success": 0, "skipped": 0, "errors": []}

    for row_idx, row in enumerate(ws.iter_rows(min_row=2), start=2):
        name = row[name_col].value if name_col < len(row) else None
        phone = row[phone_col].value if phone_col < len(row) else None
        group_name = row[group_col].value if group_col is not None and group_col < len(row) else ""

        if not name or not phone:
            result["skipped"] += 1
            continue

        name = str(name).strip()
        phone = str(phone).strip()
        group_name = str(group_name).strip() if group_name else ""

        # 去除电话号码可能的小数点（Excel 数字格式）
        if phone.endswith(".0"):
            phone = phone[:-2]

        try:
            add_contact(name=name, phone=phone, group_name=group_name)
            result["success"] += 1
        except Exception as e:
            result["errors"].append(f"第{row_idx}行导入失败: {e}")

    wb.close()
    return result


def _find_column(headers: list[str], keywords: list[str]) -> int | None:
    """在表头中查找匹配关键词的列索引。"""
    for i, h in enumerate(headers):
        for kw in keywords:
            if kw in h:
                return i
    return None
