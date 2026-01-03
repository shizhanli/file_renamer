from __future__ import annotations

import csv
import os
import uuid
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

    existing_names = {p.name for p in items}
    planned_targets: set[str] = set()
    counter_by_second: dict[str, int] = {}

    for p in items:
      st = p.stat()
      mtime = st.st_mtime
      ts = format_ts(mtime)

      counter_by_second[ts] = counter_by_second.get(ts, 0) + 1
      seq = counter_by_second[ts]

      new_name = f"{ts}_{seq:02d}{p.suffix}"
      mtime_iso = datetime.fromtimestamp(mtime).isoformat(timespec="seconds")

      if new_name == p.name:
        status = "SKIP"
        note = "already named"
      elif new_name in planned_targets:
        status = "SKIP"
        note = "duplicate target in plan"
      elif new_name in existing_names:
        status = "SKIP"
        note = "target exists"
      else:
        status = "PLAN"
        note = ""

      planned_targets.add(new_name)

      plan.append(
        PlanItem(
          folder=str(folder),
          old_name=p.name,
          new_name=new_name,
          mtime_iso=mtime_iso,
          status=status,
          note=note,
        )
      )

  return plan


def write_report(repo_root: Path, prefix: str, plan: List[PlanItem]) -> Path:
  reports_dir = repo_root / "reports"
  reports_dir.mkdir(parents=True, exist_ok=True)

  stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
  report_path = reports_dir / f"{prefix}_{stamp}.csv"

  with report_path.open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["folder", "old_name", "new_name", "mtime", "status", "note"])
    for item in plan:
      w.writerow([item.folder, item.old_name, item.new_name, item.mtime_iso, item.status, item.note])

  return report_path


def summarize(plan: List[PlanItem]) -> dict[str, int]:
  counts: dict[str, int] = {}
  for item in plan:
    counts[item.status] = counts.get(item.status, 0) + 1
  counts["TOTAL"] = len(plan)
  return counts


def print_summary(title: str, counts: dict[str, int]) -> None:
  print(title)
  print(f"總檔案數: {counts.get('TOTAL', 0)}")
  print(f"可改名數: {counts.get('PLAN', 0)}")
  print(f"已完成數: {counts.get('DONE', 0)}")
  print(f"跳過數: {counts.get('SKIP', 0)}")
  print(f"錯誤數: {counts.get('ERROR', 0)}")


def apply_plan(plan: List[PlanItem]) -> None:
  by_folder: dict[Path, List[PlanItem]] = {}
  for item in plan:
    by_folder.setdefault(Path(item.folder), []).append(item)

  for folder, items in sorted(by_folder.items(), key=lambda x: str(x[0])):
    to_apply = [x for x in items if x.status == "PLAN"]
    if not to_apply:
      continue

    used_names = {p.name for p in folder.iterdir() if p.is_file()}
    temp_pairs: list[tuple[PlanItem, str]] = []

    for item in to_apply:
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

      suffix = Path(item.old_name).suffix
      token = uuid.uuid4().hex
      tmp_name = f"renamer_tmp_{token}{suffix}"

      while tmp_name in used_names or (folder / tmp_name).exists():
        token = uuid.uuid4().hex
        tmp_name = f"renamer_tmp_{token}{suffix}"

      used_names.add(tmp_name)
      temp_pairs.append((item, tmp_name))

    for item, tmp_name in temp_pairs:
      if item.status != "PLAN":
        continue
      src = folder / item.old_name
      tmp = folder / tmp_name
      try:
        src.rename(tmp)
      except Exception as e:
        item.status = "ERROR"
        item.note = f"temp rename failed: {e}"

    for item, tmp_name in temp_pairs:
      if item.status != "PLAN":
        continue
      tmp = folder / tmp_name
      dst = folder / item.new_name

      if dst.exists():
        item.status = "ERROR"
        item.note = "target exists after temp step"
        continue

      try:
        tmp.rename(dst)
        item.status = "DONE"
        item.note = ""
      except Exception as e:
        item.status = "ERROR"
        item.note = f"final rename failed: {e}"


def main() -> None:
  repo_root = Path(__file__).resolve().parent.parent

  path_str = input("請輸入要處理的資料夾路徑: ").strip()
  mode = input("請輸入模式 preview 或 apply: ").strip().lower()

  if mode not in ("preview", "apply"):
    print("模式只能是 preview 或 apply")
    return

  root = Path(path_str).expanduser().resolve()
  if not root.exists() or not root.is_dir():
    print("路徑不存在或不是資料夾")
    return

  plan = build_plan(root)

  preview_report = write_report(repo_root, "preview", plan)
  preview_counts = summarize(plan)
  print_summary("預覽結果", preview_counts)
  print(f"已輸出預覽報表: {preview_report}")

  if mode == "preview":
    print("preview 完成")
    return

  confirm = input("即將執行改名，是否繼續 (y 或 yes 才會執行): ").strip().lower()
  if confirm not in ("y", "yes"):
    print("已取消，未進行改名")
    return

  apply_plan(plan)

  apply_report = write_report(repo_root, "apply", plan)
  apply_counts = summarize(plan)
  print_summary("套用結果", apply_counts)
  print(f"已輸出執行報表: {apply_report}")


if __name__ == "__main__":
  main()
