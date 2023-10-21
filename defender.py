from pokemon import Pokemon


class Defender:
    dps = 900

    def __init__(self, type_1: str = '', type_2: str = '', defender_mon: Pokemon = None):
        self.pokemon = defender_mon
        self.type_1 = type_1
        self.type_2 = type_2
        if self.pokemon is not None:
            self.type_1 = self.pokemon.type_1
            self.type_2 = self.pokemon.type_2
            self.defense = (self.pokemon.base_defn + 15) * 0.7903
            self.atk = (self.pokemon.base_atk + 15) * 0.7903
        else:
            self.defense = 160
        self.fast_move = None
        self.charged_move = None
