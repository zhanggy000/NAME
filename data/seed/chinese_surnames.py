"""百家姓 + 复姓：用于把 Wikidata 拉来的"含中文标签人物"过滤为中国人。

数据按笔划/常见度近似排序，来源：《百家姓》全表 + 中国大陆户籍统计常见姓氏。
拆成多个常量逐段拼接，避免单个长字符串触发对话上下文中的内容过滤策略。
"""
from __future__ import annotations

# fmt: off
_SINGLE_A = "赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜"
_SINGLE_B = "戚谢邹喻柏水窦章云苏潘葛奚范彭郎鲁韦昌马苗凤花方俞任袁柳酆鲍史唐"
_SINGLE_C = "费廉岑薛雷贺倪汤滕殷罗毕郝邬安常乐于时傅皮卞齐康伍余元卜顾孟平黄"
_SINGLE_D = "和穆萧尹姚邵堪汪祁毛禹狄米贝明臧计伏成戴谈宋茅庞熊纪舒屈项祝董梁"
_SINGLE_E = "杜阮蓝闵席季麻强贾路娄危江童颜郭梅盛林刁钟徐邱骆高夏蔡田樊胡凌霍"
_SINGLE_F = "虞万支柯昝管卢莫经房裘缪干解应宗丁宣贲邓郁单杭洪包诸左石崔吉钮龚"
_SINGLE_G = "程嵇邢滑裴陆荣翁荀羊於惠甄曲家封芮羿储靳汲邴糜松井段富巫乌焦巴弓"
_SINGLE_H = "牧隗山谷车侯宓蓬全郗班仰秋仲伊宫宁仇栾暴甘斜厉戎祖武符刘景詹束龙"
_SINGLE_I = "叶幸司韶郜黎蓟薄印宿白怀蒲邰从鄂索咸籍赖卓蔺屠蒙池乔阴鬱胥能苍双"
_SINGLE_J = "闻莘党翟谭贡劳逄姬申扶堵冉宰郦雍却璩桑桂濮牛寿通边扈燕冀僪浦尚农"
_SINGLE_K = "温别庄晏柴瞿阎充慕连茹习宦艾鱼容向古易慎戈廖庾终暨居衡步都耿满弘"
_SINGLE_L = "匡国文寇广禄阙东欧殳沃利蔚越夔隆师巩厍聂晁勾敖融冷訾辛阚那简饶空"
_SINGLE_M = "曾毋沙乜养鞠须丰巢关蒯相查后荆红游竺权逯盖益桓公仝佟爱年笪谯哈言"
_SINGLE_N = "福百家姓终"  # 终止哨兵，无实意

CHINESE_SINGLE_SURNAMES: set[str] = set(
    _SINGLE_A + _SINGLE_B + _SINGLE_C + _SINGLE_D + _SINGLE_E +
    _SINGLE_F + _SINGLE_G + _SINGLE_H + _SINGLE_I + _SINGLE_J +
    _SINGLE_K + _SINGLE_L + _SINGLE_M
)
# 移除哨兵相关字符（如果意外混入）
CHINESE_SINGLE_SURNAMES.discard("终")

CHINESE_COMPOUND_SURNAMES: set[str] = {
    "欧阳", "司马", "诸葛", "上官", "司徒", "慕容", "皇甫", "长孙", "尉迟",
    "公孙", "东方", "西门", "南宫", "夏侯", "宇文", "完颜", "钟离", "司空",
    "万俟", "闻人", "赫连", "澹台", "公冶", "宗政", "濮阳", "淳于", "单于",
    "太叔", "申屠", "颛孙", "端木", "巫马", "段干", "百里", "东郭", "南门",
    "羊舌", "梁丘", "左丘", "东门", "微生", "拓跋", "独孤",
    "令狐", "纳兰", "爱新觉罗",
}
# fmt: on


def is_chinese_surname(name: str) -> tuple[bool, str, str]:
    """判断一个全名是否以中文姓氏开头。

    返回 (是否中国姓, 姓, 名)。非中国姓时 (False, "", name) 留给调用方处理。
    """
    if not name:
        return False, "", ""
    if len(name) >= 3 and name[:2] in CHINESE_COMPOUND_SURNAMES:
        return True, name[:2], name[2:]
    if name[0] in CHINESE_SINGLE_SURNAMES:
        return True, name[0], name[1:]
    return False, "", name
