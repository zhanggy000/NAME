"""
单字字典种子数据（核心常用取名字）

格式：每条字典记录一个汉字的元数据。
字段：
    char, pinyin, tone, kangxi, simplified, wuxing,
    radical, meaning, gender_pref, style_tags, classics_refs, famous_refs

注：
- kangxi 笔画为康熙繁体笔画（取名数理用此）
- wuxing 取主流共识，置信度低的在 note 字段标明
- classics_refs 与 famous_refs 是简化的内联引用，正式入库时会拆到 character_classics / character_famous

本种子表覆盖 ~200 个高频取名字，作为算法开发的基础数据。
完整 5000+ 字库由 scripts/import_characters.py 从外部数据源批量导入。
"""

CHARACTERS_SEED = [
    # ============== 常见姓氏（用于五格计算）==============
    {"char": "张", "pinyin": "zhāng", "tone": 1, "kangxi": 11, "simplified": 7,
     "wuxing": "火", "radical": "弓", "meaning": "姓氏（張）",
     "gender_pref": "中性", "style_tags": []},
    {"char": "王", "pinyin": "wáng", "tone": 2, "kangxi": 4, "simplified": 4,
     "wuxing": "土", "radical": "王", "meaning": "姓氏",
     "gender_pref": "中性", "style_tags": []},
    {"char": "李", "pinyin": "lǐ", "tone": 3, "kangxi": 7, "simplified": 7,
     "wuxing": "木", "radical": "木", "meaning": "姓氏",
     "gender_pref": "中性", "style_tags": []},
    {"char": "刘", "pinyin": "liú", "tone": 2, "kangxi": 15, "simplified": 6,
     "wuxing": "金", "radical": "刂", "meaning": "姓氏（劉）",
     "gender_pref": "中性", "style_tags": []},
    {"char": "陈", "pinyin": "chén", "tone": 2, "kangxi": 16, "simplified": 7,
     "wuxing": "火", "radical": "阝", "meaning": "姓氏（陳）",
     "gender_pref": "中性", "style_tags": []},
    {"char": "杨", "pinyin": "yáng", "tone": 2, "kangxi": 13, "simplified": 7,
     "wuxing": "木", "radical": "木", "meaning": "姓氏（楊）",
     "gender_pref": "中性", "style_tags": []},
    {"char": "黄", "pinyin": "huáng", "tone": 2, "kangxi": 12, "simplified": 11,
     "wuxing": "土", "radical": "黄", "meaning": "姓氏（黃）",
     "gender_pref": "中性", "style_tags": []},
    {"char": "赵", "pinyin": "zhào", "tone": 4, "kangxi": 14, "simplified": 9,
     "wuxing": "火", "radical": "走", "meaning": "姓氏（趙）",
     "gender_pref": "中性", "style_tags": []},
    {"char": "周", "pinyin": "zhōu", "tone": 1, "kangxi": 8, "simplified": 8,
     "wuxing": "金", "radical": "口", "meaning": "姓氏",
     "gender_pref": "中性", "style_tags": []},
    {"char": "吴", "pinyin": "wú", "tone": 2, "kangxi": 7, "simplified": 7,
     "wuxing": "木", "radical": "口", "meaning": "姓氏（吳）",
     "gender_pref": "中性", "style_tags": []},
    {"char": "欧", "pinyin": "ōu", "tone": 1, "kangxi": 15, "simplified": 8,
     "wuxing": "土", "radical": "欠", "meaning": "姓氏（歐）",
     "gender_pref": "中性", "style_tags": []},
    {"char": "阳", "pinyin": "yáng", "tone": 2, "kangxi": 17, "simplified": 6,
     "wuxing": "土", "radical": "阝", "meaning": "姓氏（陽）",
     "gender_pref": "中性", "style_tags": []},
    {"char": "司", "pinyin": "sī", "tone": 1, "kangxi": 5, "simplified": 5,
     "wuxing": "金", "radical": "口", "meaning": "姓氏",
     "gender_pref": "中性", "style_tags": []},
    {"char": "马", "pinyin": "mǎ", "tone": 3, "kangxi": 10, "simplified": 3,
     "wuxing": "水", "radical": "马", "meaning": "姓氏（馬）",
     "gender_pref": "中性", "style_tags": []},
    {"char": "诸", "pinyin": "zhū", "tone": 1, "kangxi": 16, "simplified": 10,
     "wuxing": "金", "radical": "讠", "meaning": "姓氏（諸）",
     "gender_pref": "中性", "style_tags": []},
    {"char": "葛", "pinyin": "gě", "tone": 3, "kangxi": 15, "simplified": 12,
     "wuxing": "木", "radical": "艹", "meaning": "姓氏",
     "gender_pref": "中性", "style_tags": []},

    # ============== 火 五行（暖局调候首选）==============
    {"char": "昊", "pinyin": "hào", "tone": 4, "kangxi": 8, "simplified": 8,
     "wuxing": "火", "radical": "日", "meaning": "广大天空",
     "gender_pref": "男", "style_tags": ["大气","明朗"],
     "classics_refs": ["《诗经·小雅·巷伯》「昊天不平」"],
     "famous_refs": ["张昊（航天员）"]},

    {"char": "晟", "pinyin": "shèng", "tone": 4, "kangxi": 11, "simplified": 10,
     "wuxing": "火", "radical": "日", "meaning": "光明炽盛",
     "gender_pref": "男", "style_tags": ["大气","光明"],
     "classics_refs": [],
     "famous_refs": ["王晟（学者）"]},

    {"char": "煜", "pinyin": "yù", "tone": 4, "kangxi": 13, "simplified": 13,
     "wuxing": "火", "radical": "火", "meaning": "照耀光明",
     "gender_pref": "男", "style_tags": ["光明","典雅"],
     "classics_refs": ["《说文》「煜，熠也」"],
     "famous_refs": ["李煜（南唐后主）"]},

    {"char": "煊", "pinyin": "xuān", "tone": 1, "kangxi": 13, "simplified": 13,
     "wuxing": "火", "radical": "火", "meaning": "温暖明亮",
     "gender_pref": "男", "style_tags": ["温暖","典雅"]},

    {"char": "晗", "pinyin": "hán", "tone": 2, "kangxi": 11, "simplified": 11,
     "wuxing": "火", "radical": "日", "meaning": "天将明",
     "gender_pref": "中性", "style_tags": ["清新","婉约"]},

    {"char": "昕", "pinyin": "xīn", "tone": 1, "kangxi": 8, "simplified": 8,
     "wuxing": "火", "radical": "日", "meaning": "黎明初升的太阳",
     "gender_pref": "中性", "style_tags": ["清新","明朗"],
     "classics_refs": ["《说文》「昕，旦明也」"]},

    {"char": "昭", "pinyin": "zhāo", "tone": 1, "kangxi": 9, "simplified": 9,
     "wuxing": "火", "radical": "日", "meaning": "明显光明",
     "gender_pref": "中性", "style_tags": ["光明","正直"],
     "classics_refs": ["《诗经·大雅·抑》「昊天孔昭」"]},

    {"char": "炜", "pinyin": "wěi", "tone": 3, "kangxi": 13, "simplified": 8,
     "wuxing": "火", "radical": "火", "meaning": "光明炽盛",
     "gender_pref": "男", "style_tags": ["光明","刚毅"],
     "classics_refs": ["《诗经·邶风·静女》「彤管有炜」"]},

    {"char": "烨", "pinyin": "yè", "tone": 4, "kangxi": 14, "simplified": 10,
     "wuxing": "火", "radical": "火", "meaning": "火光盛貌",
     "gender_pref": "男", "style_tags": ["光明","大气"]},

    {"char": "晖", "pinyin": "huī", "tone": 1, "kangxi": 13, "simplified": 10,
     "wuxing": "火", "radical": "日", "meaning": "阳光光辉",
     "gender_pref": "中性", "style_tags": ["光明","温暖"],
     "classics_refs": ["孟郊《游子吟》「报得三春晖」"]},

    {"char": "敦", "pinyin": "dūn", "tone": 1, "kangxi": 12, "simplified": 12,
     "wuxing": "火", "radical": "攵", "meaning": "敦厚诚朴",
     "gender_pref": "男", "style_tags": ["厚重","君子"],
     "classics_refs": ["《论语·泰伯》「君子笃于亲」"]},

    {"char": "明", "pinyin": "míng", "tone": 2, "kangxi": 8, "simplified": 8,
     "wuxing": "火", "radical": "日", "meaning": "光明",
     "gender_pref": "中性", "style_tags": ["光明","通透"],
     "classics_refs": ["《大学》「大学之道，在明明德」"]},

    {"char": "炎", "pinyin": "yán", "tone": 2, "kangxi": 8, "simplified": 8,
     "wuxing": "火", "radical": "火", "meaning": "火光、炎热",
     "gender_pref": "男", "style_tags": ["热烈"]},

    {"char": "晋", "pinyin": "jìn", "tone": 4, "kangxi": 10, "simplified": 10,
     "wuxing": "火", "radical": "日", "meaning": "上升、进取",
     "gender_pref": "男", "style_tags": ["进取","古意"],
     "classics_refs": ["《周易·晋卦》「晋者，进也」"]},

    {"char": "朗", "pinyin": "lǎng", "tone": 3, "kangxi": 11, "simplified": 10,
     "wuxing": "火", "radical": "月", "meaning": "明朗清亮",
     "gender_pref": "男", "style_tags": ["清朗","通透"]},

    {"char": "鼎", "pinyin": "dǐng", "tone": 3, "kangxi": 13, "simplified": 12,
     "wuxing": "火", "radical": "鼎", "meaning": "鼎立、显赫",
     "gender_pref": "男", "style_tags": ["大气","厚重"],
     "classics_refs": ["《周易·鼎卦》「鼎，象也」"]},

    {"char": "智", "pinyin": "zhì", "tone": 4, "kangxi": 12, "simplified": 12,
     "wuxing": "火", "radical": "日", "meaning": "智慧",
     "gender_pref": "中性", "style_tags": ["睿智","厚重"]},

    {"char": "丹", "pinyin": "dān", "tone": 1, "kangxi": 4, "simplified": 4,
     "wuxing": "火", "radical": "丶", "meaning": "丹砂红色，赤诚",
     "gender_pref": "中性", "style_tags": ["赤诚","古典"]},

    {"char": "翎", "pinyin": "líng", "tone": 2, "kangxi": 11, "simplified": 11,
     "wuxing": "火", "radical": "羽", "meaning": "鸟翎、华美",
     "gender_pref": "女", "style_tags": ["灵动","清丽"]},

    # ============== 土 五行（培根稳固）==============
    {"char": "坤", "pinyin": "kūn", "tone": 1, "kangxi": 8, "simplified": 8,
     "wuxing": "土", "radical": "土", "meaning": "大地，柔顺",
     "gender_pref": "中性", "style_tags": ["厚重","典雅"],
     "classics_refs": ["《周易·坤卦》「地势坤，君子以厚德载物」"]},

    {"char": "城", "pinyin": "chéng", "tone": 2, "kangxi": 10, "simplified": 9,
     "wuxing": "土", "radical": "土", "meaning": "城池、稳固",
     "gender_pref": "男", "style_tags": ["稳固","大气"],
     "classics_refs": ["《诗经·大雅·板》「宗子维城」"]},

    {"char": "维", "pinyin": "wéi", "tone": 2, "kangxi": 14, "simplified": 11,
     "wuxing": "土", "radical": "纟", "meaning": "维系、思虑",
     "gender_pref": "中性", "style_tags": ["稳重","古意"],
     "classics_refs": ["《诗经·大雅·板》「宗子维城」"]},

    {"char": "轩", "pinyin": "xuān", "tone": 1, "kangxi": 10, "simplified": 7,
     "wuxing": "土", "radical": "车", "meaning": "高扬、气宇",
     "gender_pref": "男", "style_tags": ["大气","清朗"]},

    {"char": "宇", "pinyin": "yǔ", "tone": 3, "kangxi": 6, "simplified": 6,
     "wuxing": "土", "radical": "宀", "meaning": "宇宙、气宇",
     "gender_pref": "男", "style_tags": ["大气","开阔"]},

    {"char": "辰", "pinyin": "chén", "tone": 2, "kangxi": 7, "simplified": 7,
     "wuxing": "土", "radical": "辰", "meaning": "时辰、星辰",
     "gender_pref": "中性", "style_tags": ["时光","典雅"],
     "classics_refs": ["《论语·为政》「为政以德，譬如北辰」"]},

    {"char": "宸", "pinyin": "chén", "tone": 2, "kangxi": 10, "simplified": 10,
     "wuxing": "金", "radical": "宀", "meaning": "屋宇、帝王居所",
     "gender_pref": "中性", "style_tags": ["典雅","尊贵"]},

    {"char": "峻", "pinyin": "jùn", "tone": 4, "kangxi": 10, "simplified": 10,
     "wuxing": "土", "radical": "山", "meaning": "高山、峻拔",
     "gender_pref": "男", "style_tags": ["刚毅","大气"]},

    {"char": "岳", "pinyin": "yuè", "tone": 4, "kangxi": 8, "simplified": 8,
     "wuxing": "土", "radical": "山", "meaning": "高山",
     "gender_pref": "男", "style_tags": ["稳重","大气"]},

    {"char": "安", "pinyin": "ān", "tone": 1, "kangxi": 6, "simplified": 6,
     "wuxing": "土", "radical": "宀", "meaning": "平安",
     "gender_pref": "中性", "style_tags": ["平和"]},

    {"char": "尧", "pinyin": "yáo", "tone": 2, "kangxi": 12, "simplified": 6,
     "wuxing": "木", "radical": "兀", "meaning": "上古明君，高远",
     "gender_pref": "男", "style_tags": ["大气","古意"]},

    {"char": "翔", "pinyin": "xiáng", "tone": 2, "kangxi": 12, "simplified": 12,
     "wuxing": "土", "radical": "羽", "meaning": "翱翔",
     "gender_pref": "男", "style_tags": ["飞扬","清朗"],
     "classics_refs": ["《诗经·大雅·卷阿》「凤皇于飞，翙翙其羽」"]},

    {"char": "媛", "pinyin": "yuán", "tone": 2, "kangxi": 12, "simplified": 12,
     "wuxing": "土", "radical": "女", "meaning": "美女",
     "gender_pref": "女", "style_tags": ["典雅","婉约"]},

    {"char": "越", "pinyin": "yuè", "tone": 4, "kangxi": 12, "simplified": 12,
     "wuxing": "土", "radical": "走", "meaning": "超越",
     "gender_pref": "男", "style_tags": ["进取"]},

    {"char": "怡", "pinyin": "yí", "tone": 2, "kangxi": 9, "simplified": 8,
     "wuxing": "土", "radical": "忄", "meaning": "和悦愉快",
     "gender_pref": "女", "style_tags": ["温和","婉约"]},

    # ============== 金 五行 ==============
    {"char": "瑾", "pinyin": "jǐn", "tone": 3, "kangxi": 16, "simplified": 15,
     "wuxing": "火", "radical": "王", "meaning": "美玉",
     "gender_pref": "中性", "style_tags": ["典雅","婉约"],
     "classics_refs": ["《楚辞·九章·怀沙》「怀瑾握瑜兮」"]},

    {"char": "瑜", "pinyin": "yú", "tone": 2, "kangxi": 14, "simplified": 13,
     "wuxing": "金", "radical": "王", "meaning": "美玉",
     "gender_pref": "中性", "style_tags": ["典雅"],
     "famous_refs": ["周瑜（三国名将）"]},

    {"char": "锦", "pinyin": "jǐn", "tone": 3, "kangxi": 16, "simplified": 13,
     "wuxing": "金", "radical": "钅", "meaning": "锦绣华美",
     "gender_pref": "中性", "style_tags": ["华美","典雅"]},

    {"char": "钰", "pinyin": "yù", "tone": 4, "kangxi": 13, "simplified": 10,
     "wuxing": "金", "radical": "钅", "meaning": "珍宝",
     "gender_pref": "中性", "style_tags": ["珍贵"]},

    {"char": "鑫", "pinyin": "xīn", "tone": 1, "kangxi": 24, "simplified": 24,
     "wuxing": "金", "radical": "金", "meaning": "金多兴旺",
     "gender_pref": "男", "style_tags": ["兴旺"]},

    # ============== 水 五行 ==============
    {"char": "霖", "pinyin": "lín", "tone": 2, "kangxi": 16, "simplified": 16,
     "wuxing": "水", "radical": "雨", "meaning": "久雨润泽",
     "gender_pref": "中性", "style_tags": ["润泽","典雅"]},

    {"char": "涵", "pinyin": "hán", "tone": 2, "kangxi": 12, "simplified": 11,
     "wuxing": "水", "radical": "氵", "meaning": "包容涵养",
     "gender_pref": "中性", "style_tags": ["涵养","婉约"]},

    {"char": "泽", "pinyin": "zé", "tone": 2, "kangxi": 17, "simplified": 8,
     "wuxing": "水", "radical": "氵", "meaning": "恩泽光泽",
     "gender_pref": "男", "style_tags": ["恩泽"]},

    {"char": "雯", "pinyin": "wén", "tone": 2, "kangxi": 12, "simplified": 12,
     "wuxing": "水", "radical": "雨", "meaning": "云成纹理",
     "gender_pref": "女", "style_tags": ["婉约","清丽"],
     "classics_refs": ["《集韵》「雯，云成章曰雯」"],
     "famous_refs": ["刘诗雯（乒乓球世界冠军）","郑佩雯（演员）"]},

    {"char": "潇", "pinyin": "xiāo", "tone": 1, "kangxi": 20, "simplified": 14,
     "wuxing": "水", "radical": "氵", "meaning": "潇洒清雅",
     "gender_pref": "中性", "style_tags": ["洒脱"]},

    {"char": "清", "pinyin": "qīng", "tone": 1, "kangxi": 12, "simplified": 11,
     "wuxing": "水", "radical": "氵", "meaning": "清澈纯净",
     "gender_pref": "中性", "style_tags": ["清雅"]},

    {"char": "渊", "pinyin": "yuān", "tone": 1, "kangxi": 12, "simplified": 11,
     "wuxing": "水", "radical": "氵", "meaning": "深渊深邃",
     "gender_pref": "男", "style_tags": ["深邃"]},

    # ============== 木 五行 ==============
    {"char": "景", "pinyin": "jǐng", "tone": 3, "kangxi": 12, "simplified": 12,
     "wuxing": "木", "radical": "日", "meaning": "景象、光明",
     "gender_pref": "中性", "style_tags": ["大气","明朗"]},

    {"char": "彦", "pinyin": "yàn", "tone": 4, "kangxi": 9, "simplified": 9,
     "wuxing": "木", "radical": "彡", "meaning": "贤才",
     "gender_pref": "男", "style_tags": ["才德"],
     "classics_refs": ["《尔雅》「美士为彦」"]},

    {"char": "嘉", "pinyin": "jiā", "tone": 1, "kangxi": 14, "simplified": 14,
     "wuxing": "木", "radical": "口", "meaning": "嘉美吉祥",
     "gender_pref": "中性", "style_tags": ["吉祥","典雅"]},

    {"char": "芷", "pinyin": "zhǐ", "tone": 3, "kangxi": 10, "simplified": 7,
     "wuxing": "木", "radical": "艹", "meaning": "白芷香草",
     "gender_pref": "女", "style_tags": ["典雅","清雅"],
     "classics_refs": ["《楚辞·离骚》「扈江离与辟芷兮，纫秋兰以为佩」"]},

    {"char": "若", "pinyin": "ruò", "tone": 4, "kangxi": 11, "simplified": 8,
     "wuxing": "木", "radical": "艹", "meaning": "如同、若兰若水",
     "gender_pref": "中性", "style_tags": ["婉约"]},

    {"char": "蓁", "pinyin": "zhēn", "tone": 1, "kangxi": 16, "simplified": 13,
     "wuxing": "木", "radical": "艹", "meaning": "草木茂盛",
     "gender_pref": "女", "style_tags": ["典雅","古意"],
     "classics_refs": ["《诗经·桃夭》「桃之夭夭，其叶蓁蓁」"]},

    {"char": "雅", "pinyin": "yǎ", "tone": 3, "kangxi": 12, "simplified": 12,
     "wuxing": "木", "radical": "隹", "meaning": "高雅",
     "gender_pref": "中性", "style_tags": ["典雅","文气"],
     "classics_refs": ["《论语·述而》「子所雅言」"]},

    {"char": "婉", "pinyin": "wǎn", "tone": 3, "kangxi": 11, "simplified": 11,
     "wuxing": "土", "radical": "女", "meaning": "温婉柔顺",
     "gender_pref": "女", "style_tags": ["婉约","柔美"],
     "classics_refs": ["《诗经·野有蔓草》「有美一人，清扬婉兮」"]},

    {"char": "静", "pinyin": "jìng", "tone": 4, "kangxi": 16, "simplified": 14,
     "wuxing": "金", "radical": "青", "meaning": "宁静",
     "gender_pref": "女", "style_tags": ["宁静","婉约"],
     "classics_refs": ["《诗经·邶风·静女》「静女其姝」"]},

    {"char": "诗", "pinyin": "shī", "tone": 1, "kangxi": 13, "simplified": 8,
     "wuxing": "金", "radical": "讠", "meaning": "诗歌、诗意",
     "gender_pref": "女", "style_tags": ["文气","典雅"],
     "classics_refs": ["《毛诗序》「诗者，志之所之也」"],
     "famous_refs": ["刘诗雯（乒乓球世界冠军）"]},

    {"char": "语", "pinyin": "yǔ", "tone": 3, "kangxi": 14, "simplified": 9,
     "wuxing": "木", "radical": "讠", "meaning": "言语",
     "gender_pref": "女", "style_tags": ["文气","婉约"]},

    {"char": "梓", "pinyin": "zǐ", "tone": 3, "kangxi": 11, "simplified": 11,
     "wuxing": "木", "radical": "木", "meaning": "梓树（高贵之木）",
     "gender_pref": "中性", "style_tags": ["典雅","古意"]},

    {"char": "桐", "pinyin": "tóng", "tone": 2, "kangxi": 10, "simplified": 10,
     "wuxing": "木", "radical": "木", "meaning": "梧桐（凤栖之木）",
     "gender_pref": "中性", "style_tags": ["典雅","古意"]},

    {"char": "佳", "pinyin": "jiā", "tone": 1, "kangxi": 8, "simplified": 8,
     "wuxing": "木", "radical": "亻", "meaning": "美好",
     "gender_pref": "女", "style_tags": ["美好"]},

    # ============== 其他常用补充 ==============
    {"char": "紫", "pinyin": "zǐ", "tone": 3, "kangxi": 12, "simplified": 12,
     "wuxing": "金", "radical": "糸", "meaning": "紫色尊贵",
     "gender_pref": "女", "style_tags": ["尊贵","典雅"],
     "classics_refs": ["《史记·老子韩非列传》「紫气东来」"]},

    {"char": "佩", "pinyin": "pèi", "tone": 4, "kangxi": 8, "simplified": 8,
     "wuxing": "水", "radical": "亻", "meaning": "佩玉、佩戴",
     "gender_pref": "女", "style_tags": ["典雅"]},

    {"char": "如", "pinyin": "rú", "tone": 2, "kangxi": 6, "simplified": 6,
     "wuxing": "金", "radical": "女", "meaning": "如同",
     "gender_pref": "女", "style_tags": ["柔美"]},

    {"char": "之", "pinyin": "zhī", "tone": 1, "kangxi": 4, "simplified": 3,
     "wuxing": "火", "radical": "丶", "meaning": "助词、之乎者也",
     "gender_pref": "中性", "style_tags": ["古典","文气"]},

    {"char": "宥", "pinyin": "yòu", "tone": 4, "kangxi": 9, "simplified": 9,
     "wuxing": "土", "radical": "宀", "meaning": "宽容",
     "gender_pref": "男", "style_tags": ["宽厚"]},

    {"char": "皓", "pinyin": "hào", "tone": 4, "kangxi": 12, "simplified": 12,
     "wuxing": "木", "radical": "白", "meaning": "洁白光明",
     "gender_pref": "男", "style_tags": ["光明","清朗"]},

    {"char": "承", "pinyin": "chéng", "tone": 2, "kangxi": 8, "simplified": 8,
     "wuxing": "金", "radical": "手", "meaning": "承担继承",
     "gender_pref": "男", "style_tags": ["稳重"]},

    {"char": "昱", "pinyin": "yù", "tone": 4, "kangxi": 9, "simplified": 9,
     "wuxing": "火", "radical": "日", "meaning": "日光",
     "gender_pref": "男", "style_tags": ["明朗"]},

    {"char": "珂", "pinyin": "kē", "tone": 1, "kangxi": 10, "simplified": 9,
     "wuxing": "木", "radical": "王", "meaning": "美玉，马勒玉饰",
     "gender_pref": "中性", "style_tags": ["典雅","古意"]},

    {"char": "玮", "pinyin": "wěi", "tone": 3, "kangxi": 14, "simplified": 8,
     "wuxing": "土", "radical": "王", "meaning": "珍奇美玉",
     "gender_pref": "中性", "style_tags": ["珍贵","典雅"]},

    {"char": "睿", "pinyin": "ruì", "tone": 4, "kangxi": 14, "simplified": 14,
     "wuxing": "金", "radical": "目", "meaning": "睿智深远",
     "gender_pref": "男", "style_tags": ["睿智","厚重"]},

    {"char": "卓", "pinyin": "zhuó", "tone": 2, "kangxi": 8, "simplified": 8,
     "wuxing": "火", "radical": "十", "meaning": "卓越超群",
     "gender_pref": "中性", "style_tags": ["卓越"]},

    {"char": "弘", "pinyin": "hóng", "tone": 2, "kangxi": 5, "simplified": 5,
     "wuxing": "水", "radical": "弓", "meaning": "弘大",
     "gender_pref": "男", "style_tags": ["大气","古意"]},

    # ============== 扩展字库 第二批 ==============

    # 火 五行扩展
    {"char": "烁", "pinyin": "shuò", "tone": 4, "kangxi": 19, "simplified": 9,
     "wuxing": "火", "radical": "火", "meaning": "光亮",
     "gender_pref": "中性", "style_tags": ["光明"]},
    {"char": "焜", "pinyin": "kūn", "tone": 1, "kangxi": 12, "simplified": 12,
     "wuxing": "火", "radical": "火", "meaning": "明亮光辉",
     "gender_pref": "男", "style_tags": ["光明","古意"]},
    {"char": "焯", "pinyin": "zhuō", "tone": 1, "kangxi": 12, "simplified": 12,
     "wuxing": "火", "radical": "火", "meaning": "明亮",
     "gender_pref": "男", "style_tags": ["光明"]},
    {"char": "灿", "pinyin": "càn", "tone": 4, "kangxi": 17, "simplified": 7,
     "wuxing": "火", "radical": "火", "meaning": "灿烂",
     "gender_pref": "中性", "style_tags": ["华美"]},
    {"char": "曦", "pinyin": "xī", "tone": 1, "kangxi": 20, "simplified": 20,
     "wuxing": "火", "radical": "日", "meaning": "晨光",
     "gender_pref": "中性", "style_tags": ["清新","典雅"]},
    {"char": "暄", "pinyin": "xuān", "tone": 1, "kangxi": 13, "simplified": 13,
     "wuxing": "火", "radical": "日", "meaning": "温暖",
     "gender_pref": "中性", "style_tags": ["温暖"]},
    {"char": "晔", "pinyin": "yè", "tone": 4, "kangxi": 14, "simplified": 10,
     "wuxing": "火", "radical": "日", "meaning": "光耀",
     "gender_pref": "男", "style_tags": ["光明"]},
    {"char": "彤", "pinyin": "tóng", "tone": 2, "kangxi": 7, "simplified": 7,
     "wuxing": "火", "radical": "彡", "meaning": "红色",
     "gender_pref": "女", "style_tags": ["明朗","婉约"],
     "classics_refs": ["《诗经·邶风·静女》「贻我彤管」"]},
    {"char": "妍", "pinyin": "yán", "tone": 2, "kangxi": 7, "simplified": 7,
     "wuxing": "水", "radical": "女", "meaning": "美丽",
     "gender_pref": "女", "style_tags": ["婉约","美好"]},
    {"char": "晨", "pinyin": "chén", "tone": 2, "kangxi": 11, "simplified": 11,
     "wuxing": "火", "radical": "日", "meaning": "清晨",
     "gender_pref": "中性", "style_tags": ["清新","明朗"]},
    {"char": "旭", "pinyin": "xù", "tone": 4, "kangxi": 6, "simplified": 6,
     "wuxing": "火", "radical": "日", "meaning": "朝阳",
     "gender_pref": "男", "style_tags": ["明朗"]},
    {"char": "晞", "pinyin": "xī", "tone": 1, "kangxi": 11, "simplified": 11,
     "wuxing": "火", "radical": "日", "meaning": "晒干、破晓",
     "gender_pref": "中性", "style_tags": ["清新","典雅"],
     "classics_refs": ["《诗经·秦风·蒹葭》「白露未晞」"]},

    # 土 五行扩展
    {"char": "墨", "pinyin": "mò", "tone": 4, "kangxi": 15, "simplified": 15,
     "wuxing": "土", "radical": "土", "meaning": "墨色、文墨",
     "gender_pref": "男", "style_tags": ["文气","古意"]},
    {"char": "圳", "pinyin": "zhèn", "tone": 4, "kangxi": 7, "simplified": 7,
     "wuxing": "土", "radical": "土", "meaning": "田间水沟",
     "gender_pref": "男", "style_tags": []},
    {"char": "垚", "pinyin": "yáo", "tone": 2, "kangxi": 9, "simplified": 9,
     "wuxing": "土", "radical": "土", "meaning": "山高",
     "gender_pref": "男", "style_tags": ["大气","古意"]},
    {"char": "崇", "pinyin": "chóng", "tone": 2, "kangxi": 11, "simplified": 11,
     "wuxing": "土", "radical": "山", "meaning": "崇高",
     "gender_pref": "男", "style_tags": ["大气"]},
    {"char": "致", "pinyin": "zhì", "tone": 4, "kangxi": 10, "simplified": 9,
     "wuxing": "火", "radical": "至", "meaning": "致达、雅致",
     "gender_pref": "中性", "style_tags": ["典雅"]},
    {"char": "翊", "pinyin": "yì", "tone": 4, "kangxi": 11, "simplified": 11,
     "wuxing": "土", "radical": "羽", "meaning": "辅佐、飞翔",
     "gender_pref": "男", "style_tags": ["稳重"]},
    {"char": "懿", "pinyin": "yì", "tone": 4, "kangxi": 22, "simplified": 22,
     "wuxing": "土", "radical": "心", "meaning": "美好、德",
     "gender_pref": "中性", "style_tags": ["典雅","古意","厚重"]},
    {"char": "依", "pinyin": "yī", "tone": 1, "kangxi": 8, "simplified": 8,
     "wuxing": "土", "radical": "亻", "meaning": "依靠",
     "gender_pref": "女", "style_tags": ["婉约"]},
    {"char": "悠", "pinyin": "yōu", "tone": 1, "kangxi": 11, "simplified": 11,
     "wuxing": "土", "radical": "心", "meaning": "悠远闲适",
     "gender_pref": "中性", "style_tags": ["闲适","古意"],
     "classics_refs": ["《诗经·关雎》「悠哉悠哉，辗转反侧」"]},

    # 木 五行扩展
    {"char": "桓", "pinyin": "huán", "tone": 2, "kangxi": 10, "simplified": 10,
     "wuxing": "木", "radical": "木", "meaning": "桓桓威武",
     "gender_pref": "男", "style_tags": ["稳重","古意"]},
    {"char": "槿", "pinyin": "jǐn", "tone": 3, "kangxi": 15, "simplified": 14,
     "wuxing": "木", "radical": "木", "meaning": "木槿花",
     "gender_pref": "女", "style_tags": ["典雅"]},
    {"char": "栩", "pinyin": "xǔ", "tone": 3, "kangxi": 10, "simplified": 10,
     "wuxing": "木", "radical": "木", "meaning": "栩栩如生",
     "gender_pref": "中性", "style_tags": ["典雅"]},
    {"char": "楚", "pinyin": "chǔ", "tone": 3, "kangxi": 13, "simplified": 13,
     "wuxing": "木", "radical": "木", "meaning": "清晰、楚地",
     "gender_pref": "中性", "style_tags": ["古意","清雅"]},
    {"char": "棠", "pinyin": "táng", "tone": 2, "kangxi": 12, "simplified": 12,
     "wuxing": "木", "radical": "木", "meaning": "棠梨",
     "gender_pref": "女", "style_tags": ["典雅","古意"],
     "classics_refs": ["《诗经·召南·甘棠》「蔽芾甘棠」"]},
    {"char": "若", "pinyin": "ruò", "tone": 4, "kangxi": 11, "simplified": 8,
     "wuxing": "木", "radical": "艹", "meaning": "如同、若兰",
     "gender_pref": "中性", "style_tags": ["婉约"]},
    {"char": "兰", "pinyin": "lán", "tone": 2, "kangxi": 23, "simplified": 5,
     "wuxing": "木", "radical": "艹", "meaning": "兰花",
     "gender_pref": "女", "style_tags": ["典雅","清雅"],
     "classics_refs": ["《楚辞·离骚》「纫秋兰以为佩」"]},
    {"char": "茗", "pinyin": "míng", "tone": 2, "kangxi": 12, "simplified": 9,
     "wuxing": "木", "radical": "艹", "meaning": "茶名",
     "gender_pref": "中性", "style_tags": ["清新"]},
    {"char": "蕊", "pinyin": "ruǐ", "tone": 3, "kangxi": 18, "simplified": 15,
     "wuxing": "木", "radical": "艹", "meaning": "花蕊",
     "gender_pref": "女", "style_tags": ["清雅"]},
    {"char": "莹", "pinyin": "yíng", "tone": 2, "kangxi": 15, "simplified": 10,
     "wuxing": "木", "radical": "艹", "meaning": "玉光",
     "gender_pref": "女", "style_tags": ["婉约","光明"]},
    {"char": "薇", "pinyin": "wēi", "tone": 1, "kangxi": 19, "simplified": 16,
     "wuxing": "木", "radical": "艹", "meaning": "蔷薇花",
     "gender_pref": "女", "style_tags": ["婉约","古意"],
     "classics_refs": ["《诗经·小雅·采薇》「采薇采薇，薇亦作止」"]},

    # 金 五行扩展
    {"char": "镜", "pinyin": "jìng", "tone": 4, "kangxi": 19, "simplified": 16,
     "wuxing": "金", "radical": "钅", "meaning": "明镜",
     "gender_pref": "中性", "style_tags": ["典雅"]},
    {"char": "钦", "pinyin": "qīn", "tone": 1, "kangxi": 12, "simplified": 9,
     "wuxing": "金", "radical": "钅", "meaning": "钦佩、敬重",
     "gender_pref": "男", "style_tags": ["稳重"]},
    {"char": "铭", "pinyin": "míng", "tone": 2, "kangxi": 14, "simplified": 11,
     "wuxing": "金", "radical": "钅", "meaning": "铭记",
     "gender_pref": "男", "style_tags": ["稳重"]},
    {"char": "瑶", "pinyin": "yáo", "tone": 2, "kangxi": 15, "simplified": 14,
     "wuxing": "火", "radical": "王", "meaning": "美玉",
     "gender_pref": "女", "style_tags": ["典雅","清丽"]},
    {"char": "璇", "pinyin": "xuán", "tone": 2, "kangxi": 16, "simplified": 15,
     "wuxing": "火", "radical": "王", "meaning": "美玉",
     "gender_pref": "女", "style_tags": ["典雅"]},
    {"char": "璐", "pinyin": "lù", "tone": 4, "kangxi": 18, "simplified": 17,
     "wuxing": "火", "radical": "王", "meaning": "美玉",
     "gender_pref": "女", "style_tags": ["典雅"]},
    {"char": "珍", "pinyin": "zhēn", "tone": 1, "kangxi": 10, "simplified": 9,
     "wuxing": "火", "radical": "王", "meaning": "珍宝",
     "gender_pref": "女", "style_tags": ["珍贵"]},
    {"char": "珺", "pinyin": "jùn", "tone": 4, "kangxi": 12, "simplified": 11,
     "wuxing": "木", "radical": "王", "meaning": "美玉",
     "gender_pref": "中性", "style_tags": ["典雅"]},
    {"char": "瑞", "pinyin": "ruì", "tone": 4, "kangxi": 14, "simplified": 13,
     "wuxing": "金", "radical": "王", "meaning": "祥瑞",
     "gender_pref": "中性", "style_tags": ["吉祥"]},

    # 水 五行扩展
    {"char": "汐", "pinyin": "xī", "tone": 1, "kangxi": 7, "simplified": 6,
     "wuxing": "水", "radical": "氵", "meaning": "晚潮",
     "gender_pref": "女", "style_tags": ["婉约","清新"]},
    {"char": "沐", "pinyin": "mù", "tone": 4, "kangxi": 8, "simplified": 7,
     "wuxing": "水", "radical": "氵", "meaning": "沐浴、润泽",
     "gender_pref": "中性", "style_tags": ["温润"]},
    {"char": "澜", "pinyin": "lán", "tone": 2, "kangxi": 21, "simplified": 15,
     "wuxing": "水", "radical": "氵", "meaning": "波澜",
     "gender_pref": "中性", "style_tags": ["大气"]},
    {"char": "淞", "pinyin": "sōng", "tone": 1, "kangxi": 12, "simplified": 11,
     "wuxing": "水", "radical": "氵", "meaning": "淞江",
     "gender_pref": "中性", "style_tags": []},

    # 通用补充：常用且优秀的字
    {"char": "梦", "pinyin": "mèng", "tone": 4, "kangxi": 14, "simplified": 11,
     "wuxing": "木", "radical": "夕", "meaning": "梦境",
     "gender_pref": "女", "style_tags": ["梦幻"]},
    {"char": "亦", "pinyin": "yì", "tone": 4, "kangxi": 6, "simplified": 6,
     "wuxing": "土", "radical": "亠", "meaning": "也、亦然",
     "gender_pref": "中性", "style_tags": ["古意"]},
    {"char": "欣", "pinyin": "xīn", "tone": 1, "kangxi": 8, "simplified": 8,
     "wuxing": "木", "radical": "欠", "meaning": "喜悦",
     "gender_pref": "女", "style_tags": ["明朗"]},
    {"char": "妤", "pinyin": "yú", "tone": 2, "kangxi": 7, "simplified": 7,
     "wuxing": "水", "radical": "女", "meaning": "美女",
     "gender_pref": "女", "style_tags": ["典雅","古意"]},
    {"char": "婕", "pinyin": "jié", "tone": 2, "kangxi": 11, "simplified": 11,
     "wuxing": "木", "radical": "女", "meaning": "古代女官名",
     "gender_pref": "女", "style_tags": ["典雅"]},
    {"char": "嫣", "pinyin": "yān", "tone": 1, "kangxi": 14, "simplified": 14,
     "wuxing": "土", "radical": "女", "meaning": "美好",
     "gender_pref": "女", "style_tags": ["婉约","美好"]},
    {"char": "婷", "pinyin": "tíng", "tone": 2, "kangxi": 12, "simplified": 12,
     "wuxing": "火", "radical": "女", "meaning": "美好、亭亭",
     "gender_pref": "女", "style_tags": ["婉约"]},
    {"char": "馨", "pinyin": "xīn", "tone": 1, "kangxi": 20, "simplified": 20,
     "wuxing": "金", "radical": "香", "meaning": "芳香",
     "gender_pref": "女", "style_tags": ["典雅","清雅"],
     "classics_refs": ["《尚书》「黍稷非馨，明德惟馨」"]},
    {"char": "羽", "pinyin": "yǔ", "tone": 3, "kangxi": 6, "simplified": 6,
     "wuxing": "土", "radical": "羽", "meaning": "羽毛、翱翔",
     "gender_pref": "中性", "style_tags": ["飞扬"]},
    {"char": "凡", "pinyin": "fán", "tone": 2, "kangxi": 3, "simplified": 3,
     "wuxing": "水", "radical": "几", "meaning": "平凡",
     "gender_pref": "中性", "style_tags": []},
    {"char": "宁", "pinyin": "níng", "tone": 2, "kangxi": 14, "simplified": 5,
     "wuxing": "火", "radical": "宀", "meaning": "安宁",
     "gender_pref": "中性", "style_tags": ["平和","典雅"]},
    {"char": "嘉", "pinyin": "jiā", "tone": 1, "kangxi": 14, "simplified": 14,
     "wuxing": "木", "radical": "口", "meaning": "嘉美、吉祥",
     "gender_pref": "中性", "style_tags": ["吉祥","典雅"]},
    {"char": "宥", "pinyin": "yòu", "tone": 4, "kangxi": 9, "simplified": 9,
     "wuxing": "土", "radical": "宀", "meaning": "宽容",
     "gender_pref": "男", "style_tags": ["宽厚"]},
    {"char": "知", "pinyin": "zhī", "tone": 1, "kangxi": 8, "simplified": 8,
     "wuxing": "火", "radical": "矢", "meaning": "知晓",
     "gender_pref": "中性", "style_tags": ["睿智"]},
    {"char": "晏", "pinyin": "yàn", "tone": 4, "kangxi": 10, "simplified": 10,
     "wuxing": "火", "radical": "日", "meaning": "晴朗、安乐",
     "gender_pref": "中性", "style_tags": ["平和","古意"]},
    {"char": "悦", "pinyin": "yuè", "tone": 4, "kangxi": 11, "simplified": 10,
     "wuxing": "金", "radical": "忄", "meaning": "喜悦",
     "gender_pref": "女", "style_tags": ["明朗"]},
    {"char": "羽", "pinyin": "yǔ", "tone": 3, "kangxi": 6, "simplified": 6,
     "wuxing": "土", "radical": "羽", "meaning": "羽翼",
     "gender_pref": "中性", "style_tags": ["飞扬"]},
    {"char": "贺", "pinyin": "hè", "tone": 4, "kangxi": 12, "simplified": 9,
     "wuxing": "水", "radical": "贝", "meaning": "庆贺",
     "gender_pref": "男", "style_tags": ["吉祥"]},
    {"char": "宏", "pinyin": "hóng", "tone": 2, "kangxi": 7, "simplified": 7,
     "wuxing": "水", "radical": "宀", "meaning": "宏大",
     "gender_pref": "男", "style_tags": ["大气"]},
    {"char": "禹", "pinyin": "yǔ", "tone": 3, "kangxi": 9, "simplified": 9,
     "wuxing": "土", "radical": "禸", "meaning": "大禹（治水圣君）",
     "gender_pref": "男", "style_tags": ["古意","大气"]},
]


# 自动建立索引
_BY_CHAR = {c["char"]: c for c in CHARACTERS_SEED}
_BY_WUXING: dict[str, list] = {}
_BY_STROKES: dict[int, list] = {}

for c in CHARACTERS_SEED:
    _BY_WUXING.setdefault(c["wuxing"], []).append(c)
    _BY_STROKES.setdefault(c["kangxi"], []).append(c)


def get_char(ch: str) -> dict | None:
    """按字查询"""
    return _BY_CHAR.get(ch)


def find_chars(
    wuxing: str | None = None,
    kangxi: int | None = None,
    gender: str | None = None,
    style_tags: list[str] | None = None,
) -> list[dict]:
    """按条件筛选字。多条件 AND 关系。"""
    pool = CHARACTERS_SEED
    if wuxing:
        pool = [c for c in pool if c["wuxing"] == wuxing]
    if kangxi is not None:
        pool = [c for c in pool if c["kangxi"] == kangxi]
    if gender:
        # 中性字对男女都开放；性别明确的字仅限同性别
        pool = [c for c in pool
                if c["gender_pref"] == gender or c["gender_pref"] == "中性"]
    if style_tags:
        pool = [c for c in pool
                if any(t in c.get("style_tags", []) for t in style_tags)]
    return pool


if __name__ == "__main__":
    print(f"✓ 种子字库加载成功，共 {len(CHARACTERS_SEED)} 字")
    print(f"✓ 按五行分布：")
    for wx in ["木", "火", "土", "金", "水"]:
        chars = _BY_WUXING.get(wx, [])
        print(f"  {wx}: {len(chars)} 字 - {[c['char'] for c in chars[:8]]}...")

    print(f"\n查询「雯」字：")
    info = get_char("雯")
    print(f"  康熙{info['kangxi']}画 / {info['wuxing']}行 / {info['meaning']}")
    print(f"  典籍：{info['classics_refs']}")
    print(f"  名人：{info['famous_refs']}")

    print(f"\n筛选「12 画 + 火/土 + 男」候选：")
    res = []
    for wx in ["火", "土"]:
        res += find_chars(wuxing=wx, kangxi=12, gender="男")
    print(f"  {[c['char'] for c in res]}")
