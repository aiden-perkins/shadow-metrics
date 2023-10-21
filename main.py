from metrics import Metrics
from pokemon_metrics import PokemonMetrics
from defender import Defender


def main():
    metrics = Metrics(hidden_power=False)
    metrics.update_gms()
    top_x_sorted(metrics.top_attackers_for_type('water', 3))


def top_x_sorted(pkm_list: list[list[PokemonMetrics, float]], amount: int = 100):
    pkm_list.sort(key=lambda x: x[1], reverse=True)
    print(f'{" X." : >2} {"pokemon" : <32} | {"fast move" : <22} | {"charge move" : <22} | ER')
    for i in range(amount):
        thing = pkm_list[i]
        fm_name = thing[0].fast_move.name + '^' if thing[0].elite_fast_move else thing[0].fast_move.name
        cm_name = thing[0].charged_move.name + '^' if thing[0].elite_charged_move else thing[0].charged_move.name
        print(f'{i + 1 : >2}. {thing[0].name : <32} | {fm_name : <22} | {cm_name : <22} | {thing[1]}')


if __name__ == '__main__':
    main()
