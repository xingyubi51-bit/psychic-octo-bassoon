#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TXT导出脚本：UTF-8带BOM，CRLF换行。

用法：
    python export_txt.py 输入文件 输出文件            # 设定类文件：只统一编码与换行
    python export_txt.py 输入文件 输出文件 --chapter  # 章节：首行标题不缩进，
                                                      # 正文每段首行缩进两个全角空格，段间空一行
"""
import sys


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    chapter = "--chapter" in sys.argv
    if len(args) != 2:
        print(__doc__)
        return 2
    src, dst = args
    with open(src, "rb") as f:
        raw = f.read().decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    if chapter:
        lines = [ln.replace("\u3000", "").strip() for ln in raw.split("\n")]
        lines = [ln for ln in lines if ln]
        out = [lines[0]] + ["\u3000\u3000" + ln for ln in lines[1:]]
        text = "\n\n".join(out) + "\n"
    else:
        text = raw if raw.endswith("\n") else raw + "\n"
    with open(dst, "wb") as f:
        f.write(b"\xef\xbb\xbf" + text.replace("\n", "\r\n").encode("utf-8"))
    print(f"已导出：{dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
