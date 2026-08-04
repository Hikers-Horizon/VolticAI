from pathlib import Path
path = Path("app/ai/engine.py")
text = path.read_text(encoding="utf-8")
start = text.index("        factors = self._score_factors(snap)")
end = text.index("    # ── Factor scoring")
new = Path("_analyze_block.py").read_text(encoding="utf-8")
path.write_text(text[:start] + new + text[end:], encoding="utf-8")
print("OK analyze patched", start, end)
