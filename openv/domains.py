"""Static domain registry: one implementation, no plugin framework."""
from pathlib import Path
from typing import Protocol

from openv.core import DesignVersion, HardwareSystem, Method


class Domain(Protocol):
    id: str
    def methods(self) -> list[Method]: ...
    def define(self, proposal, mission_text: str) -> tuple[HardwareSystem, DesignVersion]: ...
    def patch(self, design: DesignVersion, changes: dict[str,float], experiment_id: str) -> DesignVersion: ...
    def build(self, design: DesignVersion, scenario: dict, directory: Path) -> dict: ...
    def context(self, hardware: HardwareSystem, design: DesignVersion, artifacts: dict) -> dict: ...
    def pending_context(self, context: dict, candidate: DesignVersion) -> dict: ...
    def read_seed(self, seed: dict): ...
    def branch(self, seed: dict, proposal) -> tuple[HardwareSystem, DesignVersion]: ...
    def package(self, folder: Path, hardware: HardwareSystem, design: DesignVersion, artifacts: dict) -> dict: ...


class AircraftDomain:
    id="motor-glider/1"

    def package(self,folder,hardware,design,artifacts):
        from openv.aircraft_package import write_package
        return write_package(folder,hardware,design,artifacts)

    def read_seed(self,seed):
        from openv.engineer import MissionProposal
        return MissionProposal.model_validate(seed["definition"])

    def branch(self,seed,proposal):
        from openv.aircraft import initial_design
        from openv.core import digest
        hardware=HardwareSystem.model_validate(seed["system"])
        if seed["origin"]["mission_amended"]:
            # Preserve the accepted contracts. Only mission-derived thresholds
            # explicitly amended by the user may change across this branch.
            thresholds={"mass":proposal.mission.max_mass_kg,"endurance":proposal.mission.endurance_min}
            requirements=tuple(r.model_copy(update={"contracts":tuple(
                c.model_copy(update={"threshold":thresholds[r.id]}) for c in r.contracts)})
                if r.id in thresholds else r for r in hardware.requirements)
            hardware=hardware.model_copy(update={"scenario":proposal.mission.model_dump(),
                "requirements":requirements,"baseline_id":"baseline-"+digest({
                    "parent":hardware.baseline_id,"mission":proposal.mission.model_dump(),
                    "requirements":[r.model_dump() for r in requirements]})[:12]})
        return hardware,initial_design(hardware,proposal.parameters)

    def methods(self):
        from openv import aircraft,cad
        from openv import propulsion
        return aircraft.methods()+[cad.method(),Method("propulsion","uiuc-measured-propeller-and-energy/1",
            ("geometry","mass_properties","scenario","catalog","propeller_profile"),propulsion.output)]

    def define(self,proposal,mission_text):
        from openv import aircraft
        from openv.core import Requirement,digest
        mission=proposal.mission.model_copy(update={"text":mission_text})
        hardware=aircraft.system(mission)
        extra=tuple(Requirement(id=f"uncovered-{i+1}",statement=clause,level="mission",owner="aircraft",
            contracts=(),origin="uncovered user clause") for i,clause in enumerate(proposal.uncovered_clauses))
        hardware=hardware.model_copy(update={"requirements":hardware.requirements+extra})
        if extra:
            hardware=hardware.model_copy(update={"baseline_id":"baseline-"+digest({
                "scenario":hardware.scenario,"requirements":[r.model_dump() for r in hardware.requirements]})[:12]})
        return hardware,aircraft.initial_design(hardware,proposal.parameters)

    def patch(self,design,changes,experiment_id):
        from openv.aircraft import patched
        return patched(design,changes,experiment_id)

    def build(self,design,scenario,directory):
        from openv.cad import build
        return build(design.parameters,scenario,directory)

    def context(self,hardware,design,artifacts):
        from openv.aircraft import MATERIALS
        from openv.propulsion import profile
        import aerosandbox
        density=float(aerosandbox.Atmosphere(altitude=hardware.scenario["altitude_m"]).density())
        return {"geometry":design.parameters,"mass_properties":artifacts["mass_properties"],
            "scenario":hardware.scenario,"materials":MATERIALS,
            "catalog":[c.model_dump() for c in hardware.components],"cad_checks":artifacts["checks"],
            "propeller_profile":profile(hardware.scenario["cruise_mps"],density)}

    def pending_context(self,context,candidate):
        return {**context,"geometry":candidate.parameters,"mass_properties":{"pending_design":candidate.id},
                "cad_checks":{"pending_design":candidate.id}}


def get_domain(name="motor-glider/1") -> Domain:
    if name!=AircraftDomain.id:
        raise ValueError(f"Unsupported domain {name}; register an implementation before running its engineering checks")
    return AircraftDomain()
