import time
import Levenshtein
from lev.session import lev
from fmt.handler import fmt_handler


def commit(result: str) -> None:
    if result:
        return fmt_handler(result)


def find_best(query: str, length: int) -> tuple[int, str]:
    distance = len(query)
    best_result = ''
    if length > 100:
        length = 100

    for key in lev.len_map[length]:
        d = Levenshtein.distance(query, key)
        if d < distance:
            distance = d
            best_result = lev.len_map[length][key]
            # if d == 0:
            #     break
            # impossible
    return distance, best_result


def search(query: str) -> None:
    if not query or query == lev.last_query:
        # nothing to do / already committed
        return None

    d = Levenshtein.distance(query, lev.last_query)
    if len(query) / d < 0.1:
        # too similar
        return None

    lev.last_query = query
    if query in lev.map:
        # this is O(1)
        exact_result = lev.map[query]
        lev.last_result = exact_result
        return commit(exact_result)

    length = len(query)
    # first find the best result in the same length
    distance, best_result = find_best(query, length)
    # commit now if good enough
    if distance < int(length // 5):
        lev.last_result = best_result
        commit(best_result)

    # continue to try
    theoretical_minimum_distance = 1
    while theoretical_minimum_distance < len(query):
        upper = length + theoretical_minimum_distance
        lower = length - theoretical_minimum_distance
        to_find_len = []
        if upper <= 100:
            to_find_len.append(upper)
        if lower > 0:
            to_find_len.append(lower)
        for length in to_find_len:
            d, result = find_best(query, length)
            if d < distance:
                distance = d
                best_result = result

        theoretical_minimum_distance += 1
        if theoretical_minimum_distance >= distance:
            # no need to continue
            break

    if lev.last_result != best_result:
        lev.last_result = best_result
        return commit(best_result)


def debug_search(query: str) -> None:
    t0 = time.perf_counter()
    search(query)
    t = time.perf_counter() - t0
    print(f'{t:.3f}s')
