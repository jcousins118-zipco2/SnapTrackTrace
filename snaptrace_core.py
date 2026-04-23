# snaptrace_core.py

  import hashlib
  import json
  import os
  from dataclasses import dataclass
  from datetime import datetime, timezone
  from typing import List, Optional


  LEDGER_PATH = "snaptrace_ledger.jsonl"
  HEAD_PATH = "snaptrace_head.json"


  def utc_now_iso():
      return datetime.now(timezone.utc).isoformat()


  def sha256_hex(s: str) -> str:
      return hashlib.sha256(s.encode("utf-8")).hexdigest()


  def compute_hash(index, timestamp, kind, prev_hash, text):
      material = f"{index}\n{timestamp}\n{kind}\n{prev_hash}\n{text}"
      return sha256_hex(material)


  @dataclass
  class Entry:
      index: int
      timestamp: str
      kind: str
      text: str
      prev_hash: str
      hash: str


  class SnapTrace:
      def __init__(self):
          self.entries: List[Entry] = []
          self.base_index: Optional[int] = None
          self._load()

      def _load(self):
          if os.path.exists(LEDGER_PATH):
              with open(LEDGER_PATH, "r", encoding="utf-8") as f:
                  for line in f:
                      d = json.loads(line)
                      self.entries.append(Entry(**d))

          if os.path.exists(HEAD_PATH):
              with open(HEAD_PATH, "r") as f:
                  self.base_index = json.load(f).get("base_index")

          if self.entries and self.base_index is None:
              self.base_index = self.entries[-1].index

      def _save(self):
          with open(LEDGER_PATH, "w", encoding="utf-8") as f:
              for e in self.entries:
                  f.write(json.dumps(e.__dict__) + "\n")

          with open(HEAD_PATH, "w") as f:
              json.dump({"base_index": self.base_index}, f)

      def tail(self):
          return self.entries[-1].index if self.entries else None

      def add(self, text, kind="note"):
          if self.base_index is not None and self.base_index < self.tail():
              return False, "HALT: base < tail (fork prevention)"

          idx = len(self.entries)
          ts = utc_now_iso()
          prev = "GENESIS" if idx == 0 else self.entries[-1].hash
          h = compute_hash(idx, ts, kind, prev, text)

          entry = Entry(idx, ts, kind, text, prev, h)
          self.entries.append(entry)
          self.base_index = idx
          self._save()

          return True, f"Committed #{idx}"

      def activate(self, idx):
          if idx < 0 or idx > self.tail():
              return False, "Invalid index"
          self.base_index = idx
          self._save()
          return True, f"Activated base={idx}"

      def clear(self):
          self.base_index = self.tail()
          self._save()

      def get_active(self):
          if self.base_index is None:
              return []
          return [e for e in self.entries if e.index <= self.base_index]

      def status(self):
          return {
              "base": self.base_index,
              "tail": self.tail()
          }
  