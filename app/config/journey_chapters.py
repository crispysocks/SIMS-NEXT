"""
西游取经游戏关卡配置
每个章节包含：剧情描述、妖怪、学习知识点、选择分支
"""

CHAPTERS = [
    {
        "chapter": 1,
        "name": "长安出发",
        "description": "唐太宗贞观十三年，唐僧受诏于长安，启程西行取经。",
        "monster": {
            "name": "无",
            "description": "此去山高路远，需小心谨慎。",
        },
        "knowledge": {
            "title": "唐三藏的来历",
            "content": "唐僧本名陈玄奘，是唐太宗李世民的御弟。因感大唐缺少大乘佛法，誓愿西行取经，历经万难，终得正果。",
        },
        "choices": [
            {"text": "拜别唐王，虔诚发誓：此去不取真经，誓不回还", "karma": 10, "success": True},
            {"text": "收拾行囊，带足盘缠，细细规划路线", "karma": 5, "success": True},
            {"text": "犹豫不决，问卜于天地", "karma": 0, "success": True},
        ],
    },
    {
        "chapter": 2,
        "name": "双叉岭遇险",
        "description": "唐僧行至双叉岭，遇到猛虎吞噬侍从，与随从失散，独自面对荒野。",
        "monster": {
            "name": "猛虎",
            "description": "山林猛虎拦住去路，饥肠辘辘，虎视眈眈。",
        },
        "knowledge": {
            "title": "古代取经者的艰险",
            "content": "古时取经者需穿越无人戈壁、翻越雪山、渡过急流。西行之路九死一生，非有坚定信仰者不能成行。",
        },
        "choices": [
            {"text": "紧闭双眼，念诵观音圣号，祈求庇佑", "karma": 10, "success": True},
            {"text": "拾起木棍自卫，谨慎后退", "karma": 5, "success": True},
            {"text": "惊惶失措，四处奔逃", "karma": -5, "success": False},
        ],
    },
    {
        "chapter": 3,
        "name": "五行山收悟空",
        "description": "唐僧路过五行山，救出被压在山下的齐天大圣孙悟空，悟空拜唐僧为师，护驾西行。",
        "monster": {
            "name": "孙悟空",
            "description": "五百年前大闹天宫的齐天大圣，被观音点化，等待取经人解救。",
        },
        "knowledge": {
            "title": "孙悟空的前世今生",
            "content": "孙悟空由补天顽石化身，学得七十二变、筋斗云。大闹天宫后被如来压在五行山下，后经观音点化，护送唐僧取经，终成斗战胜佛。",
        },
        "choices": [
            {"text": "亲手移除山石，为悟空解开封印", "karma": 10, "success": True},
            {"text": "先问明来历，再决定是否相救", "karma": 5, "success": True},
            {"text": "担心悟空野性难驯，犹豫不决", "karma": 0, "success": True},
        ],
    },
    {
        "chapter": 4,
        "name": "黑风山降熊罴",
        "description": "师徒行至黑风山，遇熊罴怪偷食仙衣，唐僧险些受害，悟空请来观音收伏此怪。",
        "monster": {
            "name": "熊罴怪",
            "description": "黑风山妖怪，身披鳞甲，力大无穷，占据山中寺院，偷食观音院僧人的仙衣。",
        },
        "knowledge": {
            "title": "黑风山与熊罴怪",
            "content": "熊罴怪本是一只黑熊精，在黑风山修行，与寺院僧人为邻。一日盗走锦斓袈裟，悟空追查至山洞，最终请观音收服，点化为守山神。",
        },
        "choices": [
            {"text": "让悟空请观音菩萨相助", "karma": 10, "success": True},
            {"text": "师徒设伏，智取妖怪", "karma": 5, "success": True},
            {"text": "绕道而行，避开此难", "karma": 0, "success": False},
        ],
    },
    {
        "chapter": 5,
        "name": "高老庄收八戒",
        "description": "取经路过高老庄，悟空降服霸占猪小姐的妖怪，原来是天蓬元帅猪八戒，劝其拜唐僧为师。",
        "monster": {
            "name": "猪八戒",
            "description": "天蓬元帅因醉酒调戏嫦娥被贬下凡，错投猪胎，占据高老庄。",
        },
        "knowledge": {
            "title": "天蓬元帅猪八戒",
            "content": "猪八戒原是天庭天蓬元帅，掌管天河十万水军。因醉酒后调戏霓裳仙子被贬下凡，错投猪胎而生。他性格憨厚、爱吃懒做，却也是取经路上不可或缺的帮手。",
        },
        "choices": [
            {"text": "以慈悲为怀，接纳八戒为徒", "karma": 10, "success": True},
            {"text": "先考验其诚心，再决定收留", "karma": 5, "success": True},
            {"text": "嫌弃其相貌丑陋，不肯收留", "karma": -5, "success": False},
        ],
    },
    {
        "chapter": 6,
        "name": "流沙河收沙僧",
        "description": "师徒来到流沙河，遇到颈戴九骷髅的妖怪，悟空联手猪八戒也不能取胜，后观音派木叉行者收伏，原来也是天界卷帘大将。",
        "monster": {
            "name": "沙僧",
            "description": "卷帘大将因打碎玻璃盏被贬下凡，在流沙河为妖，颈戴九颗取经人的骷髅。",
        },
        "knowledge": {
            "title": "卷帘大将沙悟净",
            "content": "沙僧原是天庭卷帘大将，因在蟠桃会上打碎琉璃盏被贬下凡，在流沙河成妖。他颈间挂着九颗前世取经人的骷髅，是一段悲凉的因缘。后观音点化，拜唐僧为师，法号沙悟净。",
        },
        "choices": [
            {"text": "以佛理感化，接纳沙僧为三弟子", "karma": 10, "success": True},
            {"text": "让悟空去请观音出面调和", "karma": 5, "success": True},
            {"text": "畏惧流沙河险恶，绕道而行", "karma": 0, "success": False},
        ],
    },
    {
        "chapter": 7,
        "name": "白虎岭三打白骨精",
        "description": "白虎岭上，白骨精化身民女、老妇、老翁，三次欺骗唐僧，悟空识破将打死。唐僧误以为悟空滥杀无辜，将悟空逐走。",
        "monster": {
            "name": "白骨精",
            "description": "白虎岭尸魔，擅长变化人形，摄食唐僧肉以图长生不老。",
        },
        "knowledge": {
            "title": "白骨精与三打白骨精",
            "content": "白骨精是白虎岭上的尸魔，修行千年，擅长取人形貌。她三次变化接近唐僧，第一次变少女，第二次变老妇，第三次变老翁，每次都被悟空识破击打。唐僧不辨人妖，认为悟空滥杀，将悟空逐走。",
        },
        "choices": [
            {"text": "相信悟空的火眼金睛，合力降妖", "karma": 10, "success": True},
            {"text": "谨慎求证，不轻信任何人", "karma": 5, "success": True},
            {"text": "被表象迷惑，责怪悟空", "karma": -10, "success": False},
        ],
    },
    {
        "chapter": 8,
        "name": "三借芭蕉扇",
        "description": "火焰山阻路，悟空向铁扇公主借芭蕉扇灭火，铁扇公主不借，悟空三借方成。",
        "monster": {
            "name": "铁扇公主",
            "description": "牛魔王之妻，拥有能灭火焰山的芭蕉扇，因红孩儿之事与悟空结仇。",
        },
        "knowledge": {
            "title": "火焰山与芭蕉扇",
            "content": "火焰山是孙悟空大闹天宫时踢翻八卦炉，炉火落下形成的。方圆八百里火焰，只有铁扇公主的芭蕉扇能灭火。铁扇公主最初不肯借扇，后经悟空变成牛魔王模样骗扇、最终托金刚等相助，方才借得真扇。",
        },
        "choices": [
            {"text": "亲身前往铁扇公主处，诚心相求", "karma": 10, "success": True},
            {"text": "设法寻找其他灭火的法子", "karma": 5, "success": True},
            {"text": "强取豪夺，不管后果", "karma": -5, "success": False},
        ],
    },
    {
        "chapter": 9,
        "name": "女儿国奇遇",
        "description": "师徒误入女儿国，唐僧误饮子母河水，悟空取来落胎泉水解救。女王欲招唐僧为夫，唐僧以信仰为由婉拒。",
        "monster": {
            "name": "蝎子精",
            "description": "在女儿国附近为妖，曾在雷音寺听佛说法，后逃走下界，尾巴毒针厉害无比。",
        },
        "knowledge": {
            "title": "女儿国与子母河",
            "content": "女儿国位于西梁国，国中尽是女子，喝了城外子母河的水便能成孕。猪八戒和唐僧都误饮了河水，悟空前往取来落胎泉水解救。女王见唐僧貌美，欲以国招亲，唐僧以取经大业为重婉拒。",
        },
        "choices": [
            {"text": "坚守取经信念，不为富贵所动", "karma": 10, "success": True},
            {"text": "感念女王恩情，妥善告别", "karma": 5, "success": True},
            {"text": "犹豫动摇，心生绮想", "karma": -5, "success": False},
        ],
    },
    {
        "chapter": 10,
        "name": "真假美猴王",
        "description": "六耳猕猴化作悟空模样，打伤唐僧、抢走行李，欲取代取经。悟空四处求证，终于请如来分辨真假。",
        "monster": {
            "name": "六耳猕猴",
            "description": "混世四猴之一，善聆音，能察理，知未来，能知千里一切事，皆不能去。",
        },
        "knowledge": {
            "title": "混世四猴与真假美猴王",
            "content": "六耳猕猴是混世四猴之一，能知千里外之事，模仿能力极强。他化作悟空的模样，抢走唐僧的行李，想取代取经。天上地下无人能辨真假，最终只有如来佛能识破，六耳猕猴被如来金钵罩住，现出原形。",
        },
        "choices": [
            {"text": "去西天雷音寺，求如来佛祖辨明真相", "karma": 10, "success": True},
            {"text": "请观音菩萨帮忙辨别", "karma": 5, "success": True},
            {"text": "放弃取经，任由假悟空为之", "karma": -10, "success": False},
        ],
    },
    {
        "chapter": 11,
        "name": "三借芭蕉扇续",
        "description": "悟空再借芭蕉扇，扇灭火焰山，师徒继续西行。",
        "monster": {
            "name": "牛魔王",
            "description": "平天大圣，与孙悟空曾结为兄弟，后因红孩儿与悟空结仇，拒不借扇。",
        },
        "knowledge": {
            "title": "牛魔王与平天大圣",
            "content": "牛魔王是孙悟空在花果山时的结拜兄弟，素有'平天大圣'之称。他与铁扇公主成婚后居住在火焰山附近。红孩儿被观音收服后，牛魔王对悟空怀恨在心，不肯借扇。后悟空联合金刚等众神，收服牛魔王，铁扇公主终于出借芭蕉扇。",
        },
        "choices": [
            {"text": "联合众神，收服牛魔王", "karma": 10, "success": True},
            {"text": "以情动人，劝说铁扇公主", "karma": 5, "success": True},
            {"text": "强行过山，不顾危险", "karma": -5, "success": False},
        ],
    },
    {
        "chapter": 12,
        "name": "取得真经",
        "description": "历经九九八十一难，师徒终于到达灵山雷音寺，如来传经，唐僧师徒取得真经返回大唐。",
        "monster": {
            "name": "无",
            "description": "取经大业圆满完成。",
        },
        "knowledge": {
            "title": "九九八十一难",
            "content": "唐僧师徒历时十四年，途经一百余国，行程十万八千里，终于在灵山雷音寺从如来处取得三藏真经。观音菩萨查难簿，发现唐僧所受灾难方满八十一难，尚缺一难未满，遂令揭谛赶上八大金刚，制造最后一难，归途晒经时经卷粘破一角，此为第八十一难。",
        },
        "choices": [
            {"text": "跪拜如来，感恩戴德，叩谢传经", "karma": 10, "success": True},
            {"text": "拜谢诸天神佛，答谢一路相助", "karma": 5, "success": True},
            {"text": "心中惶恐，不知如何回报", "karma": 0, "success": True},
        ],
    },
]


def get_chapter(chapter_num: int) -> dict | None:
    """根据章节号获取章节配置"""
    for ch in CHAPTERS:
        if ch["chapter"] == chapter_num:
            return ch
    return None


def get_first_chapter() -> dict:
    """获取第一章"""
    return CHAPTERS[0]


def get_chapters_count() -> int:
    """获取总章节数"""
    return len(CHAPTERS)