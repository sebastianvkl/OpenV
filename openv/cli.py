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
    args=parser.parse_args()
    if not 0<=args.max_experiments<=5:
        parser.error("max-experiments must be 0..5")
    from openv.engineer import AstraEngineer, FixtureEngineer
    from openv.pipeline import Pipeline
    from openv.core import uid
    engineer=FixtureEngineer() if args.offline else AstraEngineer()
    directory=Path(os.environ.get("OPENV_ARTIFACTS","artifacts"))/(args.run_id or uid("run"))
    if (directory/"run.json").exists():
        parser.error("Run ID already exists; evidence is not overwritten")
    state=Pipeline(directory,engineer).run(args.mission,args.max_experiments)
    print(f"{state['status']}: {state.get('gate','UNKNOWN')} / {state['stop_reason']}")
    print(directory/"run.json")


if __name__=="__main__":
    main()

