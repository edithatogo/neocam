"""Profile the active v6 exact model; historical ML remains optional."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.statewide import load_sites,select_sites
from src.pathways_v6 import compare_v6,sample_v6
def main():
    sites=select_sites(load_sites(),'spokes')
    for seed in (20261027,20261028,20261029):
        x,e=sample_v6(n=50000,seed=seed)
        result=compare_v6(sites,inputs=x,structural_draws=e)
        print(result['panda']['net_saving'].mean())
if __name__=='__main__':main()
