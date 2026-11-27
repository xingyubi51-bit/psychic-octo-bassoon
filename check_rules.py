#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《请问您是业主吗》章节自查脚本
用法：python check_rules.py 第001章_xxx.txt [更多文件...]
文件格式：第一行为标题，其余为正文；段与段之间可空行，也可不空行。
读取编码自动兼容 UTF-8 / UTF-8-BOM。
退出码：有 FAIL 返回 1，否则 0。
"""
import re
import sys

# ---------------- 可调参数 ----------------
MIN_CHARS, MAX_CHARS = 2200, 3400          # 章字数范围（不含空白与标题）；下限由2700改为2200
AVG_MIN, AVG_MAX = 20, 60                  # 段均字数
PARA_HARD_MAX = 95                         # 任一段达到该字数即 FAIL
SHORT_PARA = 20                            # 连续三段不足该字数 -> FAIL
TINY_PARA = 10                             # 不足该字数的单行，限量
TINY_MAX = 8                               # 一章内允许的不足10字单行数
ONE_LINERS_MAX = 3                         # 单独成段的重击句上限（自行人工把关，这里只提示）
EXPR_PER_K = 6.0                           # 神态词密度：每千字不少于
BUT_IS_MAX = 2                             # “不是……是……”类对举，每章不超过
MEME_NOTE = "梗数量请人工把关：每章不超过3处"

EXPR_WORDS = [
    "眉", "眼", "目光", "瞳", "睫", "嘴角", "唇", "脸色", "面色", "脸", "指尖", "手指", "手心", "掌心",
    "拳", "呼吸", "喉结", "喉咙", "肩", "背", "后颈", "脖子", "牙关", "牙", "腮", "额", "鼻", "舌",
    "膝", "腿", "笑", "皱", "挑眉", "抽了一下", "发抖", "发白", "冷汗", "鸡皮疙瘩", "耸", "摇头", "点头",
    "咬", "攥", "僵", "咽", "颤",
]
BAD_PATTERNS = [
    (r"第[一二三]\s*[，、,：:].{0,40}第[二三]", "第一第二第三式排比"),
    (r"一是.{0,40}二是", "一是二是式排比"),
    (r"其一.{0,40}其二", "其一其二式排比"),
    (r"一来.{0,40}二来", "一来二来式排比"),
    (r"[一二三四五六七八九十]盏[，、。]\s*[一二三四五六七八九十两]盏", "数字递进：X盏，X盏"),
    (r"[一二三四五六七八九十]息[。，、]\s*[一二三四五六七八九十两]息", "数字递进：X息。X息"),
    (r"(?:[一二三四五六七八九十]，){3,}", "数数式倒计时/罗列"),
]
BUT_IS_PATTERNS = [
    r"不是[^。！？\n]{1,30}[，,]\s*(?:而)?是",
    r"并非[^。！？\n]{1,30}而是",
    r"哪里是[^。！？\n]{1,30}分明是",
    r"不是[^。！？\n]{1,30}[，,]\s*只是",
]
AUTHOR_NOTE_PATTERNS = [r"作者注", r"本章要点", r"本章小结", r"【作者"]
BANNED_WORDS = ["残废", "黑鬼", "支那", "智障", "脑瘫", "婊子"]  # 针对群体/残障的辱骂词，可自行补充
# ------------------------------------------


def read_text(path):
    with open(path, "rb") as f:
        raw = f.read()
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    return raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")


def clen(s):
    return len(re.sub(r"\s+", "", s))


def split_paras(text):
    lines = [l.strip().lstrip("\u3000").strip() for l in text.split("\n")]
    lines = [l for l in lines if l]
    title, body = lines[0], lines[1:]
    return title, body


def count_quotes(p):
    return len(re.findall(r"[“「][^”」]*[”」]", p))


def check(path):
    text = read_text(path)
    title, paras = split_paras(text)
    fails, warns = [], []
    body = "".join(paras)
    total = clen(body)
    n = len(paras)
    lens = [clen(p) for p in paras]
    avg = total / n if n else 0

    # 1 字数
    if not (MIN_CHARS <= total <= MAX_CHARS):
        fails.append(f"字数 {total}，应在 {MIN_CHARS}–{MAX_CHARS}")
    # 2 段均
    if not (AVG_MIN <= avg <= AVG_MAX):
        fails.append(f"段均 {avg:.1f}，应在 {AVG_MIN}–{AVG_MAX}")
    # 3 95字以上段
    longp = [i + 1 for i, l in enumerate(lens) if l >= PARA_HARD_MAX]
    if longp:
        fails.append(f"达到{PARA_HARD_MAX}字及以上的段：第 {longp[:12]} 段，共 {len(longp)} 段")
    # 4 连续三段不足20字
    run, bad_runs = 0, []
    for i, l in enumerate(lens):
        run = run + 1 if l < SHORT_PARA else 0
        if run >= 3:
            bad_runs.append(i + 1)
    if bad_runs:
        fails.append(f"连续三段以上不足{SHORT_PARA}字，出现在第 {bad_runs[:10]} 段附近")
    # 5 不足10字单行
    tiny = [i + 1 for i, l in enumerate(lens) if l < TINY_PARA]
    if len(tiny) > TINY_MAX:
        warns.append(f"不足{TINY_PARA}字的单行 {len(tiny)} 处，偏多（建议≤{TINY_MAX}）")
    # 6 连续同长段（相邻五段极差<=6）
    flat = 0
    for i in range(len(lens) - 4):
        w = lens[i:i + 5]
        if max(w) - min(w) <= 6 and min(w) > 15:
            flat += 1
    if flat:
        warns.append(f"存在 {flat} 处连续五段几乎等长，节奏偏平，建议长短错落")
    # 7 排比与数字倒计时
    for pat, name in BAD_PATTERNS:
        hits = re.findall(pat, body)
        if hits:
            fails.append(f"命中禁用修辞「{name}」{len(hits)} 处")
    # 三项同构短句：以逗号切分的句子里，连续三个以上、各不超过6字、首字相同
    for sent in re.split(r"[。！？\n]", body):
        parts = [x.strip() for x in re.split(r"[，、,]", sent) if x.strip()]
        for i in range(len(parts) - 2):
            a, b, c = parts[i], parts[i + 1], parts[i + 2]
            if max(len(a), len(b), len(c)) <= 6 and a[0] == b[0] == c[0]:
                warns.append(f"疑似三项同构短句：{a}，{b}，{c}")
                break
    # 8 不是……是……
    bi = sum(len(re.findall(p, body)) for p in BUT_IS_PATTERNS)
    if bi > BUT_IS_MAX:
        fails.append(f"“不是……是……”类对举 {bi} 处，应≤{BUT_IS_MAX}")
    elif bi:
        warns.append(f"“不是……是……”类对举 {bi} 处（须有分量）")
    # 9 神态密度
    ex = 0
    for w in EXPR_WORDS:
        ex += body.count(w)
    dens = ex / (total / 1000) if total else 0
    if dens < EXPR_PER_K:
        fails.append(f"神态词密度 {dens:.1f}/千字，应≥{EXPR_PER_K}")
    # 10 台词段是否带神态/动作；混段嫌疑
    bare, mixed = [], []
    for i, p in enumerate(paras):
        qs = count_quotes(p)
        if qs:
            narr = re.sub(r"[“「][^”」]*[”」]", "", p)
            if clen(narr) < 4:
                bare.append(i + 1)
            # 同一段里有两个以上引号段，且引号之间的旁白出现“问/答/道/说/接着/应”，嫌疑混段
            if qs >= 2 and re.search(r"[”」][^“「]{0,20}(问|答|道|说|接话|应)[^“「]{0,12}[“「]", p):
                mixed.append(i + 1)
    if len(bare) > ONE_LINERS_MAX * 2:
        warns.append(f"光秃秃的纯台词段 {len(bare)} 个（第 {bare[:10]} 段起），请补神态与场景")
    elif bare:
        warns.append(f"纯台词段 {len(bare)} 个（第 {bare[:10]} 段），只允许章末重击句或转折")
    if mixed:
        warns.append(f"疑似两人对话塞进一段：第 {mixed[:10]} 段")
    # 11 作者注
    for pat in AUTHOR_NOTE_PATTERNS:
        if re.search(pat, text):
            fails.append(f"出现禁止内容：{pat}")
    # 12 禁用辱骂词
    for w in BANNED_WORDS:
        if w in body:
            fails.append(f"出现禁用词：{w}")
    # 13 首句核对（仅提示）
    if "第001章" in path or "第1章" in path:
        if not paras[0].startswith("凌晨两点十七分，方回对着手机说了一句收到。"):
            fails.append("第1章首句不符合约定")
    if "第660章" in path:
        if not paras[0].startswith("凌晨两点十七分，方回对着路灯说了一句收到。"):
            fails.append("第660章首句不符合约定")
        if not paras[-1].endswith("请问您是业主吗？"):
            fails.append("第660章末句不是“请问您是业主吗？”")
    # 14 统计信息
    stars = body.count("***")
    swears = len(re.findall(r"我操|卧槽|他妈", body))
    info = (f"字数 {total}｜段数 {n}｜段均 {avg:.1f}｜最长段 {max(lens) if lens else 0}｜"
            f"神态 {dens:.1f}/千字｜脏话 {swears}｜星号 {stars}｜{MEME_NOTE}")
    return title, fails, warns, info


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    any_fail = False
    for path in sys.argv[1:]:
        try:
            title, fails, warns, info = check(path)
        except Exception as e:  # noqa
            print(f"[ERROR] {path}: {e}")
            any_fail = True
            continue
        status = "FAIL" if fails else "PASS"
        print(f"[{status}] {path}  《{title}》")
        print("  " + info)
        for f in fails:
            print("  ✗ " + f)
        for w in warns:
            print("  △ " + w)
        if fails:
            any_fail = True
    sys.exit(1 if any_fail else 0)


if __name__ == "__main__":
    main()
