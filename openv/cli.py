import argparse
import os
from pathlib import Path

from dotenv import load_dotenv


def main():
    load_dotenv()
    parser=argparse.ArgumentParser(description="Run the OpenV engineering V pipeline")
    parser.add_argument("mission",nargs="?",default="Build a conventional RC motor glider carrying a 150 g camera for 20 minutes.")
    parser.add_argument("--offline",action="store_true",help="Explicit fixture proposer; real CAD and engineering calculations")
    parser.add_argument("--run-id",default=None)
    parser.add_argument("--max-experiments",type=int,default=5)
    parser.add_argument("--seed",type=Path,help="Validated canonical state prepared by the service")
    parser.add_argument("--verify-only",action="store_true")
    args=parser.parse_args()
    if not 0<=args.max_experiments<=5:
        parser.error("max-experiments must be 0..5")
    from openv.engineer import AstraEngineer, FixtureEngineer, VerificationOnlyEngineer
    from openv.pipeline import Pipeline
    from openv.core import uid
    engineer=VerificationOnlyEngineer() if args.verify_only else FixtureEngineer() if args.offline else AstraEngineer()
    directory=Path(os.environ.get("OPENV_ARTIFACTS","artifacts"))/(args.run_id or uid("run"))
    if (directory/"run.json").exists():
        parser.error("Run ID already exists; evidence is not overwritten")
    store=None
    if os.environ.get("OPENV_STORE","local")=="dalus":
        from openv.dalus_store import DalusStore
        team=os.environ.get("DALUS_TEAM_ID")
        if not team:parser.error("DALUS_TEAM_ID is required for the Dalus MCP backend")
        store=DalusStore(directory,team)
    import json
    seed=json.loads(args.seed.read_text()) if args.seed else None
    if args.verify_only and seed is None:parser.error("verify-only needs a canonical seed")
    state=Pipeline(directory,engineer,store=store).run(args.mission,0 if args.verify_only else args.max_experiments,seed=seed)
    print(f"{state['status']}: {state.get('gate','UNKNOWN')} / {state['stop_reason']}")
    print(directory/"run.json")


if __name__=="__main__":
    main()
