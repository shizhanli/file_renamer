from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class PlanItem:
  folder: str
  old_name: str
  new_name: str
  mtime_iso: str
  status: str
  note: str


TS_RE = re.compile(r"^\d{8}_\d{6}_\d{2}$")


def is_hidden_name(name: str) -> bool:
  return name.startswith(".")


def is_temp_name(name: str) -> bool:
  return name.startswith("renamer_tmp_")


def format_ts(mtime: float) -> str:
  dt = datetime.fromtimestamp(mtime)
  return dt.strftime("%Y%m%d_%H%M%S")


def mtime_iso(mtime: float) -> str:
  return datetime.fromtimestamp(mtime).isoformat(timespec="seconds")


def looks_like_target_name(filename: str) -> bool:
  p = Path(filename)
  stem = p.stem
  return bool(TS_RE.match(stem))


def gather_files(root: Path) -> list[Path]:
  files: list[Path] = []
  for dirpath, dirnames, filenames in os.walk(root):
    dirnames[:] = [d for d in dirnames if not is_hidden_name(d)]
    for fn in filenames:
      if is_hidden_name(fn):
        continue
      if is_temp_name(fn):
        continue
      p = Path(dirpath) / fn
      if p.is_file():
        files.append(p)
  return files


def build_plan(root: Path) -> list[PlanItem]:
  all_files = gather_files(root)

  by_folder: dict[Path, list[Path]] = {}
  for p in all_files:
    by_folder.setdefault(p.parent, []).append(p)

  plan: list[PlanItem] = []

  for folder, items in sorted(by_folder.items(), key=lambda x: str(x[0])):
    items.sort(key=lambda p: (p.stat().st_mtime, p.name))

    existing_names = {p.name for p in items}
    folder_plan: list[PlanItem] = []

    counter_by_second: dict[str, int] = {}

    for p in items:
      st = p.stat()
      ts = format_ts(st.st_mtime)
      counter_by_second[ts] = counter_by_second.get(ts, 0) + 1
      seq = counter_by_second[ts]

      new_name = f"{ts}_{seq:02d}{p.suffix}"
      item = PlanItem(
        folder=str(folder),
        old_name=p.name,
        new_name=new_name,
        mtime_iso=mtime_iso(st.st_mtime),
        status="PLAN",
        note="",
      )

      if new_name == p.name:
        item.status = "SKIP"
        item.note = "already named"

      folder_plan.append(item)

    seen_targets: set[str] = set()
    for item in folder_plan:
      if item.status != "PLAN":
        continue
      if item.new_name in seen_targets:
        item.status = "SKIP"
        item.note = "duplicate target in plan"
      else:
        seen_targets.add(item.new_name)

    changed = True
    while changed:
      changed = False
      vacated = {x.old_name for x in folder_plan if x.status == "PLAN"}
      for item in folder_plan:
        if item.status != "PLAN":
          continue
        if item.new_name in existing_names and item.new_name not in vacated:
          item.status = "SKIP"
          item.note = "target exists"
          changed = True

    plan.extend(folder_plan)

  return plan


def write_report(repo_root: Path, prefix: str, plan: list[PlanItem]) -> Path:
  reports_dir = repo_root / "reports"
  reports_dir.mkdir(parents=True, exist_ok=True)

  stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
  report_path = reports_dir / f"{prefix}_{stamp}.csv"

  with report_path.open("w", newline="", encoding="utf_8_sig") as f:
    w = csv.writer(f)
    w.writerow(["folder", "old_name", "new_name", "mtime", "status", "note"])
    for item in plan:
      w.writerow([item.folder, item.old_name, item.new_name, item.mtime_iso, item.status, item.note])

  return report_path


def summarize(plan: list[PlanItem]) -> dict[str, int]:
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


def make_temp_name(used_names: set[str], suffix: str) -> str:
  while True:
    token = uuid.uuid4().hex
    tmp_name = f"renamer_tmp_{token}{suffix}"
    if tmp_name in used_names:
      continue
    used_names.add(tmp_name)
    return tmp_name


def apply_plan(plan: list[PlanItem]) -> None:
  by_folder: dict[Path, list[PlanItem]] = {}
  for item in plan:
    by_folder.setdefault(Path(item.folder), []).append(item)

  for folder, items in sorted(by_folder.items(), key=lambda x: str(x[0])):
    to_apply = [x for x in items if x.status == "PLAN"]
    if not to_apply:
      continue

    if not folder.exists() or not folder.is_dir():
      for item in to_apply:
        item.status = "ERROR"
        item.note = "folder missing"
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
      tmp_name = make_temp_name(used_names, suffix)
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
      src = folder / item.old_name

      if not tmp.exists():
        item.status = "ERROR"
        item.note = "temp file missing"
        continue

      if dst.exists():
        item.status = "ERROR"
        item.note = "target exists after temp step"
        try:
          if not src.exists():
            tmp.rename(src)
            item.note = "target exists after temp step, rolled back"
        except Exception as e:
          item.note = f"target exists after temp step, rollback failed: {e}"
        continue

      try:
        tmp.rename(dst)
        item.status = "DONE"
        item.note = ""
      except Exception as e:
        item.status = "ERROR"
        item.note = f"final rename failed: {e}"
        try:
          if tmp.exists() and not src.exists():
            tmp.rename(src)
            item.note = f"final rename failed: {e}, rolled back"
        except Exception as e2:
          item.note = f"final rename failed: {e}, rollback failed: {e2}"


def parse_args() -> argparse.Namespace:
  p = argparse.ArgumentParser(description="Rename files by mtime with preview/apply modes and CSV reports.")
  p.add_argument("--path", default=None, help="要處理的資料夾路徑，未提供則改用互動輸入")
  p.add_argument("--mode", default=None, choices=["preview", "apply"], help="preview 或 apply，未提供則改用互動輸入")
  return p.parse_args()


def main() -> None:
  args = parse_args()
  repo_root = Path(__file__).resolve().parent.parent

  if args.path is None:
    path_str = input("請輸入要處理的資料夾路徑: ").strip()
  else:
    path_str = str(args.path).strip()

  if args.mode is None:
    mode = input("請輸入模式 preview 或 apply: ").strip().lower()
  else:
    mode = str(args.mode).strip().lower()

  if mode not in ("preview", "apply"):
    print("模式只能是 preview 或 apply")
    return

  root = Path(path_str).expanduser().resolve()
  if not root.exists() or not root.is_dir():
    print("路徑不存在或不是資料夾")
    return

  plan = build_plan(root)

  preview_report = write_report(repo_root, "preview", plan)
  print_summary("預覽結果", summarize(plan))
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
  print_summary("套用結果", summarize(plan))
  print(f"已輸出執行報表: {apply_report}")


if __name__ == "__main__":
  try:
    main()
  except KeyboardInterrupt:
    print("\n已中止")
    sys.exit(130)
