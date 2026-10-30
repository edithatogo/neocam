"""Measure duplicate-work removal on the same suite; optional plugins are explicit."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import re
import statistics
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]


def summarise(rows: list[dict]) -> dict:
    """Reject failed/non-equivalent samples instead of cherry-picking timings."""
    if not rows or any(row['returncode'] != 0 for row in rows):
        raise ValueError('All timed samples must pass')
    if len({row['passed'] for row in rows}) != 1:
        raise ValueError('Benchmarked suites are not equivalent')
    groups={name:[r['duration_seconds'] for r in rows if r['variant']==name]
            for name in {r['variant'] for r in rows}}
    if not {'old','new'} <= groups.keys():
        raise ValueError('Both baseline and new implementation are required')
    med={name:statistics.median(values) for name,values in groups.items()}
    return {'median_seconds':med,'speedup':med['old']/med['new'],
            'reduction_fraction':1-med['new']/med['old'],
            'tests_per_run':rows[0]['passed'],
            'scope':'Same available host; no claim about full online CI'}


def timed(commands: list[tuple[str,...]], log: Path) -> dict:
    """Time serial commands and require matching positive passed-test counts."""
    if not commands:
        raise ValueError("At least one benchmark command is required")
    log = log if log.is_absolute() else ROOT / log
    log.parent.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    counts = []
    exitcode = 0
    with log.open("w", encoding="utf-8") as stream:
        for command in commands:
            stream.write("COMMAND: " + repr(command) + "\n")
            stream.flush()
            offset = stream.tell()
            try:
                result = subprocess.run(command, cwd=ROOT, stdout=stream,
                    stderr=subprocess.STDOUT, text=True, check=False, timeout=180)
                code = result.returncode
            except subprocess.TimeoutExpired:
                stream.write("\nBENCHMARK TIMEOUT; this is not a timing sample\n")
                code = 124
            stream.flush()
            with log.open(encoding="utf-8") as readback:
                readback.seek(offset)
                output = readback.read()
            found = re.search(r"(\d+) passed", output)
            counts.append(int(found.group(1)) if found else 0)
            if code or not found:
                exitcode = code or 1
                break
    if len(set(counts)) != 1:
        exitcode = 1
    return {"duration_seconds": time.perf_counter() - start,
        "returncode": exitcode, "passed": counts[-1],
        "log": str(log.relative_to(ROOT))}


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repeats',type=int,default=3)
    args=parser.parse_args()
    if args.repeats<2:parser.error('At least two repetitions are required')
    out=ROOT/'verification/v4/benchmarks';out.mkdir(parents=True,exist_ok=True)
    plain=(sys.executable,'-m','pytest','-q')
    covered=(sys.executable,'-m','coverage','run','-m','pytest','-q')
    samples=[]
    # Alternate order to reduce systematic warm-up/order bias.
    for i in range(args.repeats):
        variants=('old','new') if i%2==0 else ('new','old')
        for variant in variants:
            result=timed([plain,covered] if variant=='old' else [covered],out/f'{variant}_{i}.txt')
            samples.append({'variant':variant,'repeat':i,**result})
            print(variant,i,round(result['duration_seconds'],3),result['returncode'],flush=True)
    optional={}
    for package in ('xdist','testmon'):
        optional[package]='available; not yet benchmark-qualified' if importlib.util.find_spec(package) else 'blocked: package unavailable'
    report={'samples':samples,'optional':optional,'summary':summarise(samples),'python':sys.version}
    (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['summary'],indent=2))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
