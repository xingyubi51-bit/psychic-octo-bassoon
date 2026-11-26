#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《请问您是业主吗》章节自查脚本

用法：
    python check_rules.py 第01章_请问您是业主吗.txt
    python check_rules.py chapters/*.txt
    python check_rules.py --no-length 草稿.txt      # 不检查字数

约定：
    · 文件第一行为标题，不计入统计。
    · 以“段”为单位，空行忽略；全角空格缩进会被剔除。
    · FAIL：必须重写。WARN：人工复核。
    · 退出码：有FAIL返回1，否则返回0。
"""
import re
import sys
import glob

# ---------------- 参数 ----------------
BODY_MIN, BODY_MAX = 2600, 3400      # 字数
AVG_MIN, AVG_MAX = 20, 60            # 段均字数
LONG_PARA = 95                       # 单段上限（达到即FAIL）
SHORT_PARA = 10                      # 不足即视为“极短单行”
VERY_SHORT_LIMIT = 3                 # 极短单行每章上限（超出WARN）
FACE_DENSITY_MIN = 6.0               # 每千字神态词下限
NAKED_LIMIT = 3                      # 裸台词段上限
CURSE_MIN, CURSE_MAX = 4, 16         # 脏话建议区间
NOT_BUT_FAIL = 3                     # “不是……是……”超过此数FAIL，2处以内放行
# --------------------------------------

FACE_WORDS = [
    # 人面神态
    "眉", "眼", "目光", "视线", "嘴角", "嘴唇", "唇色", "脸色", "喉结", "指尖",
    "手心", "掌心", "呼吸", "肩", "后颈", "额角", "太阳穴", "牙关", "鼻翼",
    "睫毛", "下巴", "耳根", "拳头", "脊背", "后背", "冷汗", "瞳孔", "腮帮",
    "指节", "喉咙", "鼻尖", "额头", "手腕", "腿肚",
    # 非人体征
    "指示灯", "进度环", "屏幕", "盖子", "外壳", "按钮", "灯带", "电流声",
    "喇叭", "铰链", "触须", "裂纹", "灯光", "红灯", "绿灯", "电流",
]
ACTION_WORDS = [
    "看", "盯", "望", "瞥", "抬", "低头", "点头", "摇头", "摆手", "抓", "拍",
    "指", "攥", "按", "缩", "退", "笑", "叹", "咳", "咽", "咬", "皱", "挑",
    "闪", "转", "抖", "晃", "颤", "僵", "愣", "歪", "挠", "蹭", "揉", "捂",
]
CURSE_RE = re.compile(r"我操|我草|卧槽|妈的|他妈|傻逼|操你妈|傻\*+|操\*{3}|他\*{3}")
BANNED = ["智障", "脑残", "残废", "黑鬼", "棒子", "小日本", "娘炮", "婊子", "死gay", "尼哥"]

# 排比与数字倒计时
P_ORDINAL = re.compile(r"(第一|其一|一是|一来)[\s\S]{0,300}?(第二|其二|二是|二来)")
P_COUNT = [
    re.compile(r"一[盏息步声下滴次个口][，。、\s]*[两二][盏息步声下滴次个口]"),
    re.compile(r"[一二三四五六七八九十][，。、][二两三四五六七八九十][，。、][三四五六七八九十]"),
    re.compile(r"([九八七六五四三二一])[，。、\s]*([八七六五四三二一])[，。、\s]*([七六五四三二一])"),
]
NOT_BUT = [
    re.compile(r"不是[^。！？\n“”]{1,30}[，,](?:而)?是"),
    re.compile(r"并非[^。！？\n]{1,30}而是"),
    re.compile(r"哪里是[^。！？\n]{1,30}分明是"),
    re.compile(r"不是[^。！？\n]{1,30}只是"),
]
AUTHOR_NOTE = re.compile(r"^(作者注|作者的话|本章要点|【作者|后记|附：|注：)")

FACE_RE = re.compile("|".join(sorted(map(re.escape, FACE_WORDS), key=len, reverse=True)))


def load(path):
    with open(path, "rb") as f:
        raw = f.read().decode("utf-8-sig")
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    lines = [ln.replace("\u3000", "").strip() for ln in raw.split("\n")]
    lines = [ln for ln in lines if ln]
    if not lines:
        return "", []
    return lines[0], lines[1:]


def clen(s):
    return len(re.sub(r"\s", "", s))


def repeated_starts(paras):
    """三连同首检测：相邻三个短分句以相同两字开头。"""
    hits = []
    for p in paras:
        clauses = [c for c in re.split(r"[，。！？；、\n]", p) if c]
        for i in range(len(clauses) - 2):
            a, b, c = clauses[i], clauses[i + 1], clauses[i + 2]
            if all(2 <= len(x) <= 14 for x in (a, b, c)):
                if a[:2] == b[:2] == c[:2]:
                    hits.append("、".join((a, b, c)))
    return hits


def check(path, use_length=True):
    title, paras = load(path)
    fails, warns, infos = [], [], []
    if not paras:
        return ["文件无正文"], [], []

    text = "\n".join(paras)
    total = clen(text)
    lens = [clen(p) for p in paras]
    avg = sum(lens) / len(lens)

    # 字数
    if use_length:
        if total < BODY_MIN or total > BODY_MAX:
            warns.append(f"字数{total}，建议{BODY_MIN}-{BODY_MAX}")
    infos.append(f"字数{total} 段数{len(paras)}")

    # 段均
    if avg < AVG_MIN or avg > AVG_MAX:
        fails.append(f"段均{avg:.1f}字，要求{AVG_MIN}-{AVG_MAX}")
    infos.append(f"段均{avg:.1f}")

    # 长段
    long_idx = [i + 1 for i, n in enumerate(lens) if n >= LONG_PARA]
    if long_idx:
        fails.append(f"{len(long_idx)}段达到{LONG_PARA}字以上，段序号：{long_idx[:10]}")

    # 连续短段
    run, bad_runs = 0, 0
    for n in lens:
        if n < 20:
            run += 1
            if run == 3:
                bad_runs += 1
        else:
            run = 0
    if bad_runs:
        fails.append(f"连续三段不足20字，出现{bad_runs}次")

    # 极短单行
    very_short = sum(1 for n in lens if n < SHORT_PARA)
    if very_short > VERY_SHORT_LIMIT:
        warns.append(f"不足{SHORT_PARA}字的单行有{very_short}段，建议不超过{VERY_SHORT_LIMIT}")
    for i in range(len(lens) - 1):
        if lens[i] < SHORT_PARA and lens[i + 1] < SHORT_PARA:
            warns.append(f"极短单行连用，位置第{i + 1}、{i + 2}段")
            break

    # 神态密度
    face_cnt = len(FACE_RE.findall(text))
    density = face_cnt / total * 1000 if total else 0
    infos.append(f"神态{face_cnt}处 密度{density:.1f}/千字")
    if density < FACE_DENSITY_MIN:
        fails.append(f"神态词密度{density:.1f}/千字，要求不少于{FACE_DENSITY_MIN}")

    # 排比
    if P_ORDINAL.search(text):
        fails.append("命中序数排比（第一…第二/一是…二是/其一…其二/一来…二来），请人工复核后改写")
    for rx in P_COUNT:
        m = rx.search(text)
        if m:
            fails.append(f"疑似数字倒计时或数数：“{m.group(0)}”")
            break
    rs = repeated_starts(paras)
    if rs:
        warns.append(f"疑似三连同首并列，共{len(rs)}处，例：{rs[0]}")

    # 不是……是……
    nb = 0
    for rx in NOT_BUT:
        nb += len(rx.findall(text))
    infos.append(f"不是…是…命中{nb}")
    if nb >= NOT_BUT_FAIL:
        fails.append(f"“不是……是……”类句式{nb}处，每三章合计最多保留两处")
    elif nb == 2:
        warns.append("“不是……是……”类句式2处，请确认确有分量")

    # 裸台词与带神态
    quote_paras = [p for p in paras if "“" in p]
    naked = [p for p in paras if re.fullmatch(r"[“「][^”」]*[”」]", p) and clen(p) <= 40]
    if len(naked) > NAKED_LIMIT:
        fails.append(f"裸台词（整段只有一句引语）{len(naked)}段，上限{NAKED_LIMIT}")
    no_face = 0
    for p in quote_paras:
        if not FACE_RE.search(p) and not any(w in p for w in ACTION_WORDS):
            no_face += 1
    if quote_paras and no_face / len(quote_paras) > 0.2:
        fails.append(f"台词段中有{no_face}/{len(quote_paras)}段没有神态或动作，比例超过20%")
    elif no_face:
        warns.append(f"{no_face}段台词没有神态或动作，请补")

    # 同段多人对话（粗判）
    multi = [p for p in quote_paras if p.count("“") >= 3]
    if multi:
        warns.append(f"{len(multi)}段含三处以上引语，疑似多人对话同段，请人工核对")

    # 脏话
    curses = len(CURSE_RE.findall(text))
    infos.append(f"脏话{curses}")
    if curses < CURSE_MIN:
        warns.append(f"脏话{curses}处，低于建议下限{CURSE_MIN}（可忽略，视章节而定）")
    if curses > CURSE_MAX:
        fails.append(f"脏话{curses}处，超过上限{CURSE_MAX}")

    # 禁词
    hit = [w for w in BANNED if w in text]
    if hit:
        fails.append(f"出现禁词：{hit}")

    # 作者注
    for p in paras[-8:]:
        if AUTHOR_NOTE.match(p):
            fails.append("章末出现作者注/要点类内容，请移入《伏笔表》")
            break

    return fails, warns, infos


def main(argv):
    use_length = True
    files = []
    for a in argv:
        if a == "--no-length":
            use_length = False
        else:
            files.extend(glob.glob(a))
    if not files:
        print(__doc__)
        return 2
    any_fail = False
    for f in sorted(files):
        fails, warns, infos = check(f, use_length)
        status = "FAIL" if fails else "PASS"
        any_fail = any_fail or bool(fails)
        print(f"[{status}] {f}")
        print("   指标：" + "；".join(infos))
        for x in fails:
            print("   FAIL：" + x)
        for x in warns:
            print("   WARN：" + x)
    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
