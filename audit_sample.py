"""Reproducible stratified audit selections bound to a canonical population hash."""
import argparse
import hashlib
import json
from pathlib import Path
import sys


def canonical(data):
    return json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')


def select(population, plan, seed):
    if not isinstance(population, list) or not population:
        raise ValueError('Population must be a nonempty list')
    if not isinstance(seed, str) or not seed:
        raise ValueError('A nonempty seed is required')
    ids = [row['id'] for row in population]
    if any(not isinstance(value, str) or not value for value in ids) or len(ids) != len(set(ids)):
        raise ValueError('Population IDs must be unique nonempty strings')
    if any(not isinstance(row['stratum'], str) or not row['stratum'] for row in population):
        raise ValueError('Every row needs a nonempty stratum')
    strata = {row['stratum'] for row in population}
    if not isinstance(plan, dict) or set(plan) != strata:
        raise ValueError('Plan must explicitly cover every population stratum and no others')
    ordered = sorted(population, key=lambda row: row['id'])
    population_hash = hashlib.sha256(canonical(ordered)).hexdigest()
    selections = []
    for stratum in sorted(strata):
        candidates = [row for row in ordered if row['stratum'] == stratum]
        count = plan[stratum]
        if type(count) is not int or count < 0 or count > len(candidates):
            raise ValueError(f'Invalid sample count for {stratum}')
        def score(row):
            return hashlib.sha256(canonical(['audit-sample/v1', seed, population_hash, stratum, row['id']])).hexdigest()
        ranked = sorted(candidates, key=lambda row: (score(row), row['id']))
        chosen = ranked[:count]
        selections.append({'stratum': stratum, 'population_count': len(candidates), 'sample_count': count,
                           'selected': [{'id': row['id'], 'selection_hash': score(row)} for row in chosen]})
    return {'schema': 'audit-sample/v1', 'population_sha256': population_hash, 'seed': seed,
            'plan': dict(sorted(plan.items())), 'selections': selections,
            'method': 'SHA-256 rank within each stratum; counts are supplied by the auditor.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('population', type=Path)
    parser.add_argument('plan', type=Path)
    parser.add_argument('--seed', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        population = json.loads(args.population.read_text(encoding='utf-8'))
        plan = json.loads(args.plan.read_text(encoding='utf-8'))
        result = select(population, plan, args.seed)
        with args.output.open('x', encoding='utf-8') as stream:
            stream.write(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
        return 0
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        print(f'error: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
