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


def write_report(repo_root: Path, plan: List[PlanItem]) -> Path:
  reports_dir = repo_root / "reports"
  reports_dir.mkdir(parents=True, exist_ok=True)

  stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
  report_path = reports_dir / f"preview_{stamp}.csv"

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

  root = Path(path_str).expanduser().resolve()
  if not root.exists() or not root.is_dir():
    print("路徑不存在或不是資料夾")
    return

  plan = build_plan(root)
  report_path = write_report(repo_root, plan)

  total = len(plan)
  planned = sum(1 for x in plan if x.status == "PLAN")
  skipped = total - planned

  print(f"總檔案數: {total}")
  print(f"可改名數: {planned}")
  print(f"跳過數: {skipped}")
  print(f"已輸出報表: {report_path}")

  if mode == "apply":
    print("apply 目前尚未執行改名，只先產生報表，下一步會加入真正改名流程")
  else:
    print("preview 完成")


if __name__ == "__main__":
  main()
