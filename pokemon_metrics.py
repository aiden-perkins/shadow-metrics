import json
from move import Move
from defender import Defender
from pokemon import Pokemon


class PokemonMetrics:
    _CPM_DICT = json.load(open('./data/cpm.json'))
    SHADOW_POKEMON_BONUS_MULTIPLIER = 1.2
    SAME_TYPE_ATTACK_BONUS_MULTIPLIER = 1.2
    TYPE_DICT = json.load(open('./data/type_effectiveness.json'))

    def __init__(
            self,
            pokemon: Pokemon,
            fast_move: Move,
            charged_move: Move,
            atk_iv: int = 15,
            defn_iv: int = 15,
            hp_iv: int = 15,
            level: float = 40,
            is_shadow: bool = False,
            defender: Defender = Defender(),
    ):
        self.original = pokemon
        self.name = self.original.name
        if is_shadow:
            self.name = 'shadow ' + self.name
        self.dps = 0
        self.tdo = 0
        self.er = 0
        self.fast_move = fast_move
        self.elite_fast_move = False
        self.charged_move = charged_move
        self.elite_charged_move = False

        self.atk_iv = atk_iv
        self.defn_iv = defn_iv
        self.hp_iv = hp_iv
        self.level = level

        self.is_shadow = is_shadow
        self.defender = defender

        self.atk = (self.original.base_atk + self.atk_iv) * self._CPM_DICT[self.level - 1]
        self.defn = (self.original.base_defn + self.defn_iv) * self._CPM_DICT[self.level - 1]
        self.stm = (self.original.base_stm + self.hp_iv) * self._CPM_DICT[self.level - 1]
        if self.is_shadow:
            self.atk *= self.SHADOW_POKEMON_BONUS_MULTIPLIER
            self.defn *= 0.8333333
        self.calculate_metrics()

    def set_stats(
            self, atk_iv: int = None, defn_iv: int = None, hp_iv: int = None, level: int = None, is_shadow: bool = None
    ):
        self.atk_iv = atk_iv if atk_iv is not None else self.atk_iv
        self.defn_iv = defn_iv if defn_iv is not None else self.defn_iv
        self.hp_iv = hp_iv if hp_iv is not None else self.hp_iv
        self.level = level if level is not None else self.level
        self.is_shadow = is_shadow if is_shadow is not None else self.is_shadow
        self.atk = (self.original.base_atk + self.atk_iv) * self._CPM_DICT[self.level - 1]
        self.defn = (self.original.base_defn + self.defn_iv) * self._CPM_DICT[self.level - 1]
        self.stm = (self.original.base_stm + self.hp_iv) * self._CPM_DICT[self.level - 1]
        if self.is_shadow:
            self.atk *= self.SHADOW_POKEMON_BONUS_MULTIPLIER
            self.defn *= 0.8333333
        self.calculate_metrics()

    def set_attributes(
            self,
            charged_move: Move = None,
            fast_move: Move = None,
            defender: Defender = None
    ):
        self.charged_move = charged_move if charged_move is not None else self.charged_move
        self.fast_move = fast_move if fast_move is not None else self.fast_move
        self.defender = defender if defender is not None else self.defender
        self.calculate_metrics()

    def calculate_cp(self):
        return int(max(10, self.atk * ((self.defn * self.stm) ** 0.5) / 10))

    def intake(self):
        sum_x = 0
        sum_y = 0
        f_moves = self.defender.pokemon.fast_moves
        c_moves = self.defender.pokemon.charged_moves
        if self.defender.fast_move is not None:
            f_moves = [self.defender.fast_move]
        if self.defender.charged_move is not None:
            c_moves = [self.defender.charged_move]
        for fast_move in f_moves:
            self.defender.fast_move = fast_move
            for charged_move in c_moves:
                self.defender.charged_move = charged_move
                fdmg = self.damage(self.defender.fast_move, self.defender, self.original, self.defender.atk, self.defn)
                cdmg = self.damage(
                    self.defender.charged_move, self.defender, self.original, self.defender.atk, self.defn
                )
                ce = self.defender.charged_move.energy_delta
                fdur = self.defender.fast_move.duration_s + 2
                cdur = self.defender.charged_move.duration_s + 2
                n = max(1, 3 * ce / 100)
                t = ((n * fdmg) + cdmg) / (n + 1)
                sum_x += (self.charged_move.energy_delta * 0.5) + (self.fast_move.energy_delta * 0.5) + (0.5 * t)
                sum_y += ((n * fdmg) + cdmg) / ((n * fdur) + cdur)
        total = len(f_moves) * len(c_moves)
        return {
            'x': sum_x / total,
            'y': sum_y / total
        }

    def calculate_metrics(self):
        if self.defender.pokemon is not None:
            intake = self.intake()
            x = intake['x']
            y = intake['y']
        else:
            x = (self.charged_move.energy_delta * 0.5) + (self.fast_move.energy_delta * 0.5)
            y = self.defender.dps / self.defn
        fdmg = self.damage(self.fast_move, self.original, self.defender, self.atk, self.defender.defense)
        cdmg = self.damage(self.charged_move, self.original, self.defender, self.atk, self.defender.defense)
        fe = self.fast_move.energy_delta
        ce = self.charged_move.energy_delta

        fdur = self.fast_move.duration_s
        cdur = self.charged_move.duration_s
        cdws = self.charged_move.damage_window_start_s

        if ce >= 100:
            ce = ce + 0.5 * fe + 0.5 * y * cdws

        fdps = fdmg / fdur
        feps = fe / fdur
        cdps = cdmg / cdur
        ceps = ce / cdur

        st = self.stm / y
        dps0 = (fdps * ceps + cdps * feps) / (ceps + feps)
        dps = dps0 + (((cdps - fdps) / (ceps + feps)) * (0.5 - (x / self.stm)) * y)
        tdo = dps * st

        if dps > cdps:
            dps = cdps
            tdo = dps * st
        elif dps < fdps:
            dps = fdps
            tdo = dps * st
        self.dps = dps
        self.tdo = tdo
        self.er = ((dps ** 3 * tdo) ** 0.25)

    def effectiveness(self, attacker_type: str, defender_type: str) -> float:
        return self.TYPE_DICT[attacker_type][defender_type] if defender_type != '' else 1

    def damage(
            self,
            move: Move,
            attacker: Pokemon | Defender,
            defender: Pokemon | Defender,
            attacker_atk: int,
            defender_defn: int
    ) -> float:
        multiplier = 1
        if attacker.type_1 == move.typing or attacker.type_2 == move.typing:
            multiplier *= self.SAME_TYPE_ATTACK_BONUS_MULTIPLIER
        multiplier *= self.effectiveness(move.typing, defender.type_1)
        multiplier *= self.effectiveness(move.typing, defender.type_2)
        return 0.5 * attacker_atk / defender_defn * move.power * multiplier + 0.5
