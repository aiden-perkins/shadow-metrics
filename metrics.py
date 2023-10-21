import json
import requests
import re
import copy
from move import Move
from defender import Defender
from pokemon import Pokemon
from pokemon_metrics import PokemonMetrics


def _is_different(first, second, tid):
    current = first['pokemonSettings']
    previous = second['pokemonSettings']
    if current['stats'] != previous['stats']:
        return True
    elif current['quickMoves'] != previous['quickMoves']:
        return True
    elif current['cinematicMoves'] != previous['cinematicMoves']:
        return True
    elif current['type'] != previous['type']:
        return True
    elif 'type2' in current and 'type2' in previous:
        if current['type2'] != previous['type2']:
            return True
    try:
        if 'eliteCinematicMove' in current or 'eliteCinematicMove' in previous:
            if current['eliteCinematicMove'] != previous['eliteCinematicMove']:
                return True
        if 'eliteQuickMove' in current or 'eliteQuickMove' in previous:
            if current['eliteQuickMove'] != previous['eliteQuickMove']:
                return True
    except KeyError:
        return True
    if tid in ['V0250_POKEMON_HO_OH_S', 'V0249_POKEMON_LUGIA_S']:
        return True
    return False


class Metrics:
    TYPES = [
        'fighting',
        'flying',
        'poison',
        'ground',
        'rock',
        'bug',
        'ghost',
        'steel',
        'fire',
        'water',
        'grass',
        'electric',
        'psychic',
        'ice',
        'dragon',
        'dark',
        'normal',
        'fairy'
    ]
    TYPE_DICT = json.load(open('./data/type_effectiveness.json'))
    _tids_to_exclude = [
        'V0051_POKEMON_DUGTRIO',
        'V0351_POKEMON_CASTFORM',
        'V0386_POKEMON_DEOXYS',
        'V0648_POKEMON_MELOETTA',
        'V0649_POKEMON_GENESECT',
        'V0889_POKEMON_ZAMAZENTA',
        'V0888_POKEMON_ZACIAN',
    ]
    _pokemon_without_base_stats = {  # last checked 7-8-2023
        'V0679_POKEMON_HONEDGE': {'stats': {'baseStamina': 128, 'baseAttack': 135, 'baseDefense': 139}},
        'V0680_POKEMON_DOUBLADE': {'stats': {'baseStamina': 153, 'baseAttack': 188, 'baseDefense': 206}},
        'V0681_POKEMON_AEGISLASH': {'stats': {'baseStamina': 155, 'baseAttack': 97, 'baseDefense': 291}}
    }
    _moves_without_names = {
        387: 'geomancy',
        389: 'oblivion wing',
        391: 'triple axel',
        392: 'trailblaze',
        393: 'scorching sands'
    }
    _unused_moves = [
        'wrap green',
        'wrap pink',
        'wrap green/pink',
        'water gun blastoise',
        'horn drill',
        'fissure',
        'crush claw',
        'leech life'
    ]
    _released_non_raid_ubl = [
        'V0144_POKEMON_ARTICUNO_GALARIAN',
        'V0145_POKEMON_ZAPDOS_GALARIAN',
        'V0146_POKEMON_MOLTRES_GALARIAN',
        'V0249_POKEMON_LUGIA_S',
        'V0250_POKEMON_HO_OH_S',
        'V0718_POKEMON_ZYGARDE',
        'V0718_POKEMON_ZYGARDE_COMPLETE',
        'V0718_POKEMON_ZYGARDE_COMPLETE_TEN_PERCENT',
    ]
    _unreleased_ubl = [
        'V0646_POKEMON_KYUREM_BLACK',
        'V0646_POKEMON_KYUREM_WHITE',
        'V0789_POKEMON_COSMOG',
        'V0790_POKEMON_COSMOEM',
        'V0791_POKEMON_SOLGALEO',
        'V0792_POKEMON_LUNALA',
        'V0800_POKEMON_NECROZMA',
        'V0800_POKEMON_NECROZMA_DAWN_WINGS',
        'V0800_POKEMON_NECROZMA_DUSK_MANE',
        'V0800_POKEMON_NECROZMA_ULTRA',
        'V0803_POKEMON_POIPOLE',
        'V0804_POKEMON_NAGANADEL',
        'V0805_POKEMON_STAKATAKA',
        'V0806_POKEMON_BLACEPHALON',
        'V0888_POKEMON_ZACIAN_CROWNED_SWORD',
        'V0889_POKEMON_ZAMAZENTA_CROWNED_SHIELD',
        'V0890_POKEMON_ETERNATUS',
        'V0890_POKEMON_ETERNATUS_ETERNAMAX',
        'V0891_POKEMON_KUBFU',
        'V0892_POKEMON_URSHIFU',
        'V0892_POKEMON_URSHIFU_RAPID_STRIKE',
        'V0892_POKEMON_URSHIFU_SINGLE_STRIKE',
        'V0896_POKEMON_GLASTRIER',
        'V0897_POKEMON_SPECTRIER',
        'V0898_POKEMON_CALYREX',
        'V0898_POKEMON_CALYREX_ICE_RIDER',
        'V0898_POKEMON_CALYREX_SHADOW_RIDER',
        'V1001_POKEMON_WOCHIEN',
        'V1002_POKEMON_CHIENPAO',
        'V1003_POKEMON_TINGLU',
        'V1004_POKEMON_CHIYU',
        'V1007_POKEMON_KORAIDON',
        'V1008_POKEMON_MIRAIDON',
    ]
    _released_raid_m = [
        'V0386_POKEMON_DEOXYS_ATTACK',
        'V0386_POKEMON_DEOXYS_DEFENSE',
        'V0386_POKEMON_DEOXYS_NORMAL',
        'V0386_POKEMON_DEOXYS_SPEED',
        'V0491_POKEMON_DARKRAI',
        'V0649_POKEMON_GENESECT_BURN',
        'V0649_POKEMON_GENESECT_CHILL',
        'V0649_POKEMON_GENESECT_DOUSE',
        'V0649_POKEMON_GENESECT_NORMAL',
        'V0649_POKEMON_GENESECT_SHOCK',
        'V0720_POKEMON_HOOPA_UNBOUND',
    ]

    def __init__(self, hidden_power: bool = True):
        self.gm = json.load(open('./data/pokeminers_gm.json'))
        self.move_list = self.get_list_of_moves()
        self.pokemon_list = self.get_list_of_pokemon(hidden_power=hidden_power)

    def most_effective_types(self, pokemon: Pokemon) -> list[list[str]]:
        eff_list = {}
        for typing in self.TYPES:
            current_eff_against_mon = self.TYPE_DICT[typing][pokemon.type_1]
            if pokemon.type_2 != '':
                current_eff_against_mon *= self.TYPE_DICT[typing][pokemon.type_2]
            if current_eff_against_mon not in eff_list:
                eff_list[current_eff_against_mon] = [typing]
            else:
                eff_list[current_eff_against_mon].append(typing)
        return [value for key, value in sorted(eff_list.items(), reverse=True)]

    def get_list_of_raid_weak_to(
            self,
            typing: str = None,
            include_legendary: bool = True,
            include_mythical: bool = True,
            include_mega: bool = True,
            include_ultra_beast: bool = True,
    ) -> list[Pokemon]:
        top_effective = []
        for pokemon in self.pokemon_list:
            if pokemon.mythical and not include_mythical:
                continue
            if pokemon.is_mega and not include_mega:
                continue
            if pokemon.ultra_beast and not include_ultra_beast:
                continue
            if pokemon.legendary and not include_legendary:
                continue
            if pokemon.mythical or pokemon.legendary or pokemon.ultra_beast or pokemon.is_mega:
                if pokemon.tid not in self._released_non_raid_ubl and pokemon.tid not in self._unreleased_ubl:
                    if not pokemon.mythical or pokemon.tid in self._released_raid_m:
                        eff_types = self.most_effective_types(pokemon)
                        if typing in eff_types[0] or typing is None:
                            top_effective.append(pokemon)
        return top_effective

    def top_attackers_for_type(self, typing: str, sort_by: int = 1):
        for mon in self.pokemon_list:  # Adding moves that will come to starters
            if mon.name in ['meowscarada', 'rillaboom']:
                mon.elite_charged_moves.append(self.get_move_by_name('frenzy plant'))
            elif mon.name in ['skeledirge', 'cinderace']:
                mon.elite_charged_moves.append(self.get_move_by_name('blast burn'))
            elif mon.name in ['quaquaval', 'inteleon']:
                mon.elite_charged_moves.append(self.get_move_by_name('hydro cannon'))
        all_metrics = {}
        for defender_base in self.get_list_of_raid_weak_to(typing):
            print(f'Calculating Metrics for all pokemon against {defender_base.name}...')
            for attacker_base in self.pokemon_list:
                for is_shadow in [True, False]:
                    for fast_move in attacker_base.fast_moves + attacker_base.elite_fast_moves:
                        for charged_move in attacker_base.charged_moves + attacker_base.elite_charged_moves:
                            purified_only_moves = ['return', 'sacred fire plus plus', 'aeroblast plus plus']
                            if charged_move.name in purified_only_moves and is_shadow:
                                continue
                            if charged_move.name in ['sacred fire plus', 'aeroblast plus'] and not is_shadow:
                                continue
                            if attacker_base.is_mega and is_shadow:
                                continue
                            attacker = PokemonMetrics(
                                attacker_base,
                                fast_move,
                                charged_move,
                                is_shadow=is_shadow,
                                defender=Defender(defender_mon=defender_base)
                            )
                            if charged_move in attacker_base.elite_charged_moves:
                                attacker.elite_charged_move = True
                            if fast_move in attacker_base.elite_fast_moves:
                                attacker.elite_fast_move = True
                            pid = str(is_shadow) + fast_move.name + charged_move.name
                            if attacker_base not in all_metrics:
                                all_metrics[attacker_base] = {pid: [attacker]}
                            else:
                                if pid not in all_metrics[attacker_base]:
                                    all_metrics[attacker_base][pid] = [attacker]
                                else:
                                    all_metrics[attacker_base][pid].append(attacker)
        top_average = []
        for base_pokemon in all_metrics:
            highest_average_shadow = None
            highest_metric_shadow = 0
            highest_average = None
            highest_metric = 0
            for entry in all_metrics[base_pokemon]:
                metric_sum = [0, 0, 0]
                results = all_metrics[base_pokemon][entry]
                for metric in results:
                    metric_sum[0] += metric.dps
                    metric_sum[1] += metric.tdo
                    metric_sum[2] += metric.er
                metric_sum = [x / len(results) for x in metric_sum]
                if entry.startswith('False'):
                    if metric_sum[sort_by - 1] > highest_metric:
                        highest_metric = metric_sum[sort_by - 1]
                        highest_average = results[0]
                if entry.startswith('True'):
                    if metric_sum[sort_by - 1] > highest_metric_shadow:
                        highest_metric_shadow = metric_sum[sort_by - 1]
                        highest_average_shadow = results[0]
            if highest_average_shadow is not None:
                top_average.append([highest_average_shadow, highest_metric_shadow])
            if highest_average is not None:
                top_average.append([highest_average, highest_metric])
        return top_average

    def get_original_pokemon_by_name(self, name: str):
        for pokemon in self.pokemon_list:
            if pokemon.name == name:
                return pokemon
        return None

    def hidden_power(self, list_to_add: list):
        normal_to_copy = self.get_move_by_name('hidden power')
        for typing in [
            'fighting',
            'flying',
            'poison',
            'ground',
            'rock',
            'bug',
            'ghost',
            'steel',
            'fire',
            'water',
            'grass',
            'electric',
            'psychic',
            'ice',
            'dragon',
            'dark'
        ]:
            move_copy = copy.deepcopy(normal_to_copy)
            move_copy.name += ' ' + typing
            move_copy.typing = typing
            list_to_add.append(move_copy)

    def get_list_of_pokemon(self, hidden_power: bool = True) -> list[Pokemon]:
        pm_all_moves = []
        pm_entry_pokemon_list = []
        counter = 0
        for entry in self.gm:
            tid = entry['templateId']
            if 'pokemonSettings' in entry['data'] and re.search(r'^V[0-9]{4}_POKEMON_', tid):
                pokemon_id = entry['data']['pokemonSettings']['pokemonId'].replace('_MALE', '').replace('_FEMALE', '')
                if tid in self._tids_to_exclude:
                    continue
                if pokemon_id == tid.split('_POKEMON_')[1]:
                    counter += 1
                    if counter != int(tid.split('_POKEMON_')[0][1:]):  # chespin appears here because of meloetta
                        # print(tid)
                        counter += 1
                    pm_entry_pokemon_list.append(entry['data'])
                else:
                    for added_entry in pm_entry_pokemon_list:
                        if not _is_different(entry['data'], added_entry, tid):
                            break
                    else:
                        if '_NORMAL' in tid:
                            counter += 1
                            if tid[:-7] not in self._tids_to_exclude:
                                raise Exception(f'The tid {tid} has different stats from the non-normal version')
                        pm_entry_pokemon_list.append(entry['data'])
        for pokemon in pm_entry_pokemon_list:
            if 'quickMoves' not in pokemon['pokemonSettings']:
                continue  # Smeargle doesn't have moves
            if pokemon['templateId'] in self._pokemon_without_base_stats:
                pokemon['pokemonSettings']['stats'] = self._pokemon_without_base_stats[pokemon['templateId']]['stats']
            mon = Pokemon(
                name=pokemon['templateId'].split('_POKEMON_')[1].replace('_', ' ').lower(),
                base_atk=pokemon['pokemonSettings']['stats']['baseAttack'],
                base_defn=pokemon['pokemonSettings']['stats']['baseDefense'],
                base_stm=pokemon['pokemonSettings']['stats']['baseStamina'],
                type_1=pokemon['pokemonSettings']['type'].split('POKEMON_TYPE_')[1].lower(),
            )
            if 'type2' in pokemon['pokemonSettings']:
                mon.type_2 = pokemon['pokemonSettings']['type2'].split('POKEMON_TYPE_')[1].lower()
            if 'shadow' in pokemon['pokemonSettings']:
                mon.shadow_available = True

            elite_charged = []
            if 'shadow' in pokemon['pokemonSettings']:
                elite_charged += [
                    pokemon['pokemonSettings']['shadow']['shadowChargeMove'],
                    pokemon['pokemonSettings']['shadow']['purifiedChargeMove']
                ]
            if 'eliteCinematicMove' in pokemon['pokemonSettings']:
                elite_charged += pokemon['pokemonSettings']['eliteCinematicMove']
            if not mon.shadow_available:
                elite_charged += ['RETURN']
            if 'eliteQuickMove' in pokemon['pokemonSettings']:
                elite_fast = pokemon['pokemonSettings']['eliteQuickMove']
                for move in elite_fast:
                    if move == 'HIDDEN_POWER_FAST' and hidden_power:
                        self.hidden_power(mon.elite_fast_moves)
                    else:
                        if type(move) == int:
                            move = self._moves_without_names[move] + '_fast'
                        mon.elite_fast_moves.append(self.get_move_by_name(move[:-5].replace('_', ' ').lower()))
            if 'rayquaza' in mon.name:
                elite_charged.append('dragon ascent')
            for move in pokemon['pokemonSettings']['quickMoves']:
                if move == 'HIDDEN_POWER_FAST' and hidden_power:
                    self.hidden_power(mon.fast_moves)
                else:
                    if move == 'STRUGGLE':
                        move += '_FAST'
                    if type(move) == int:
                        move = self._moves_without_names[move]
                    mon.fast_moves.append(self.get_move_by_name(move[:-5].replace('_', ' ').lower()))
            for move in pokemon['pokemonSettings']['cinematicMoves']:
                # Chimecho has psyshock twice
                # Galarian Weezing has hyper beam twice
                # Trubbish has gunk shot twice
                if type(move) == int:
                    move = self._moves_without_names[move]
                mon.charged_moves.append(self.get_move_by_name(move.lower().replace('_', ' ')))
            mon.tid = pokemon['templateId']
            for move in elite_charged:
                if type(move) == int:
                    move = self._moves_without_names[move]
                mon.elite_charged_moves.append(self.get_move_by_name(move.lower().replace('_', ' ')))
            if 'pokemonClass' in pokemon['pokemonSettings']:
                mon.legendary = True if 'LEGENDARY' in pokemon['pokemonSettings']['pokemonClass'] else False
                mon.mythical = True if 'MYTHIC' in pokemon['pokemonSettings']['pokemonClass'] else False
                mon.ultra_beast = True if 'ULTRA_BEAST' in pokemon['pokemonSettings']['pokemonClass'] else False
            if 'tempEvoOverrides' in pokemon['pokemonSettings']:
                for possible_mega in pokemon['pokemonSettings']['tempEvoOverrides']:
                    if 'tempEvoId' in possible_mega:  # why the fuck is aggron fucked up
                        mega_mon = copy.deepcopy(mon)
                        mega_mon.is_mega = True
                        mega_mon.base_atk = possible_mega['stats']['baseAttack']
                        mega_mon.base_defn = possible_mega['stats']['baseDefense']
                        mega_mon.base_stm = possible_mega['stats']['baseStamina']
                        mega_mon.type_1 = possible_mega['typeOverride1'].split('POKEMON_TYPE_')[1].lower()
                        if 'typeOverride2' in possible_mega:
                            mega_mon.type_2 = possible_mega['typeOverride2'].split('POKEMON_TYPE_')[1].lower()
                        else:
                            mega_mon.type_2 = ''
                        prefix = possible_mega['tempEvoId'].split('TEMP_EVOLUTION_')[1].lower().replace('_', ' ')
                        mega_mon.name = prefix + ' ' + mega_mon.name
                        pm_all_moves.append(mega_mon)
            pm_all_moves.append(mon)
        return pm_all_moves

    def get_list_of_moves(self) -> list[Move]:
        _moves_list = []
        for entry in self.gm:
            if re.search(r'^V[0-9]{4}_MOVE_', entry['templateId']):
                if type(entry['data']['moveSettings']['movementId']) == int:
                    name = self._moves_without_names[entry['data']['moveSettings']['movementId']]
                else:
                    name = entry['data']['moveSettings']['movementId'].lower().replace('_fast', '')
                name = name.replace('_', ' ')  # if a move has a _ replace it with a space
                if name in self._unused_moves:
                    continue
                if 'energyDelta' not in entry['data']['moveSettings']:  # Struggle
                    energy_delta = 33  # gamepress has it as 33, pvp is 100
                else:
                    energy_delta = abs(entry['data']['moveSettings']['energyDelta'])
                if 'power' not in entry['data']['moveSettings']:  # Splash, Transform, & Yawn
                    power = 0
                else:
                    power = entry['data']['moveSettings']['power']
                _moves_list.append(Move(
                    name=name,
                    typing=entry['data']['moveSettings']['pokemonType'].split('_')[2].lower(),
                    power=power,
                    energy_delta=energy_delta,
                    damage_window_start_ms=entry['data']['moveSettings']['damageWindowStartMs'],
                    damage_window_end_ms=entry['data']['moveSettings']['damageWindowEndMs'],
                    duration_ms=entry['data']['moveSettings']['durationMs']
                ))
        return _moves_list

    def get_move_by_name(self, move_name):
        for move in self.move_list:
            if move.name == move_name:
                return move
        return None

    def update_gms(self):
        pokeminers_gm_url = 'https://raw.githubusercontent.com/PokeMiners/game_masters/master/latest/latest.json'
        self.gm = requests.get(url=pokeminers_gm_url).json()
        open('./data/pokeminers_gm.json', 'w').write(json.dumps(self.gm, indent=4))
