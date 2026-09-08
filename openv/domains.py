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


class AircraftDomain:
    id="motor-glider/1"

    def methods(self):
        from openv import aircraft,cad
        from openv import propulsion
        return aircraft.methods()+[cad.method(),Method("propulsion","apc-prediction-and-energy/1",
            ("geometry","mass_properties","scenario","catalog","propeller_profile"),propulsion.output)]

    def define(self,proposal,mission_text):
        from openv import aircraft
        from openv.core import Requirement
        mission=proposal.mission.model_copy(update={"text":mission_text})
        hardware=aircraft.system(mission)
        extra=tuple(Requirement(id=f"uncovered-{i+1}",statement=clause,level="mission",owner="aircraft",
            contracts=(),origin="uncovered user clause") for i,clause in enumerate(proposal.uncovered_clauses))
        hardware=hardware.model_copy(update={"requirements":hardware.requirements+extra})
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
