from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List


@dataclass
class PlanItem:
  folder: str
  old_name: str
  new_name: str
  mtime_iso: str
  status: str
  note: str


def format_ts(mtime: float) -> str:
  dt = datetime.fromtimestamp(mtime)
  return dt.strftime("%Y%m%d_%H%M%S")


def gather_files(root: Path) -> List[Path]:
  files: List[Path] = []
  for dirpath, dirnames, filenames in os.walk(root):
    dirnames[:] = [d for d in dirnames if not d.startswith(".")]
    for fn in filenames:
      if fn.startswith("."):
        continue
      p = Path(dirpath) / fn
      if p.is_file():
        files.append(p)
  return files


def build_plan(root: Path) -> List[PlanItem]:
  all_files = gather_files(root)

  by_folder: dict[Path, List[Path]] = {}
  for p in all_files:
    by_folder.setdefault(p.parent, []).append(p)

  plan: List[PlanItem] = []

  for folder, items in sorted(by_folder.items(), key=lambda x: str(x[0])):
    items.sort(key=lambda p: (p.stat().st_mtime, p.name))

    counter_by_second: dict[str, int] = {}

    for p in items:
      mtime = p.stat().st_mtime
      ts = format_ts(mtime)
      counter_by_second[ts] = counter_by_second.get(ts, 0) + 1
      seq = counter_by_second[ts]

      new_name = f"{ts}_{seq:02d}{p.suffix}"
      target = folder / new_name

      if target.exists():
        status = "SKIP"
        note = "target exists"
      else:
        status = "PLAN"
        note = ""

      plan.append(
        PlanItem(
          folder=str(folder),
          old_name=p.name,
          new_name=new_name,
          mtime_iso=datetime.fromtimestamp(mtime).isoformat(timespec="seconds"),
          status=status,
          note=note,
        )
      )

  return plan


def apply_plan(plan: List[PlanItem]) -> None:
  for item in plan:
    if item.status != "PLAN":
      continue

    folder = Path(item.folder)
    src = folder / item.old_name
    dst = folder / item.new_name

    if not src.exists():
      item.status = "ERROR"
      item.note = "source missing"
      continue

    if dst.exists():
      item.status = "SKIP"
      item.note = "target exists"
      continue

    try:
      src.rename(dst)
      item.status = "DONE"
      item.note = ""
    except Exception as e:
      item.status = "ERROR"
      item.note = f"rename failed: {e}"


def write_report(repo_root: Path, plan: List[PlanItem], prefix: str) -> Path:
  reports_dir = repo_root / "reports"
  reports_dir.mkdir(parents=True, exist_ok=True)

  stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
  report_path = reports_dir / f"{prefix}_{stamp}.csv"

  with report_path.open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["folder", "old_name", "new_name", "mtime", "status", "note"])
    for item in plan:
      w.writerow([item.folder, item.old_name, item.new_name, item.mtime_iso, item.status, item.note])

  return report_path


def main() -> None:
  repo_root = Path(__file__).resolve().parent.parent

  path_str = input("請輸入要處理的資料夾路徑: ").strip()
  mode = input("請輸入模式 preview 或 apply: ").strip().lower()

  if mode not in ("preview", "apply"):
    print("模式輸入錯誤，請輸入 preview 或 apply")
    return

  root = Path(path_str).expanduser().resolve()
  if not root.exists() or not root.is_dir():
    print("路徑不存在或不是資料夾")
    return

  plan = build_plan(root)

  preview_report = write_report(repo_root, plan, "preview")

  total = len(plan)
  planned = sum(1 for x in plan if x.status == "PLAN")
  skipped = sum(1 for x in plan if x.status == "SKIP")
  errors = sum(1 for x in plan if x.status == "ERROR")

  print(f"總檔案數: {total}")
  print(f"可改名數: {planned}")
  print(f"跳過數: {skipped}")
  print(f"錯誤數: {errors}")
  print(f"已輸出預覽報表: {preview_report}")

  if mode == "preview":
    print("preview 完成")
    return

  confirm = input("即將執行改名，是否繼續 (y/n): ").strip().lower()
  if confirm not in ("y", "yes"):
    print("已取消，未進行改名")
    return

  apply_plan(plan)

  apply_report = write_report(repo_root, plan, "apply")

  done = sum(1 for x in plan if x.status == "DONE")
  skipped2 = sum(1 for x in plan if x.status == "SKIP")
  errors2 = sum(1 for x in plan if x.status == "ERROR")

  print(f"改名完成數: {done}")
  print(f"跳過數: {skipped2}")
  print(f"錯誤數: {errors2}")
  print(f"已輸出改名結果報表: {apply_report}")


if __name__ == "__main__":
  main()
