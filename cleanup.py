#!/usr/bin/env python3
# Cleanup script to remove duplicate code from app.py

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Keep lines 1-79 (indices 0-78), skip lines 80-650 (indices 79-649), keep from line 651+ (index 650+)
kept_lines = lines[:79] + lines[650:]

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(kept_lines)

print(f"✓ Removed duplicate code")
print(f"  - Deleted lines 80-650 ({650-79} lines)")
print(f"  - File size: {len(lines)} lines → {len(kept_lines)} lines")
