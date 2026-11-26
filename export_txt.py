#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导出 TXT：UTF-8 带 BOM，CRLF 换行。
用法：
  python export_txt.py 文件1 文件2 ... [--out out] [--chapter]
  --chapter  按章节正文格式导出：第一行标题顶格，其后每段首行缩进两个全角空格，段间空一行。
             不加该参数，则只转码与换行，内容原样保留（用于设定类文件）。
"""
import os
import sys


def read(path):
    with open(path, "rb") as f:
        raw = f.read()
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    return raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")


def to_chapter(text):
    lines = [l.strip().lstrip("\u3000").strip() for l in text.split("\n")]
    lines = [l for l in lines if l]
    if not lines:
        return ""
    out = [lines[0], ""]
    for p in lines[1:]:
        out.append("\u3000\u3000" + p)
        out.append("")
    return "\n".join(out).rstrip("\n") + "\n"


def main():
    args = sys.argv[1:]
    out_dir = "out"
    chapter = False
    files = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--out":
            out_dir = args[i + 1]
            i += 2
            continue
        if a == "--chapter":
            chapter = True
        else:
            files.append(a)
        i += 1
    if not files:
        print(__doc__)
        sys.exit(2)
    os.makedirs(out_dir, exist_ok=True)
    for f in files:
        text = read(f)
        if chapter:
            text = to_chapter(text)
        name = os.path.splitext(os.path.basename(f))[0] + ".txt"
        with open(os.path.join(out_dir, name), "wb") as w:
            w.write(b"\xef\xbb\xbf" + text.replace("\n", "\r\n").encode("utf-8"))
        print("exported", os.path.join(out_dir, name))


if __name__ == "__main__":
    main()
