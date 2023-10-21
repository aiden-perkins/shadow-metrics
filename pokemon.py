class Pokemon:

    def __init__(self, name: str, base_atk: int, base_defn: int, base_stm: int, type_1: str = '', type_2: str = ''):
        self.name = name
        self.tid = None
        self.type_1 = type_1
        self.type_2 = type_2
        self.fast_moves = []
        self.charged_moves = []
        self.elite_fast_moves = []
        self.elite_charged_moves = []
        self.available = False
        self.shadow_available = False

        self.base_atk = base_atk
        self.base_defn = base_defn
        self.base_stm = base_stm

        self.is_mega = False
        self.legendary = False
        self.mythical = False
        self.ultra_beast = False
