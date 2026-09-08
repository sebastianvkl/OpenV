import ast
import csv
import json
from types import SimpleNamespace

from openv.aircraft_package import write_package


def test_package_bom_accounts_for_installation_mass_and_regenerator_parses(tmp_path):
    geometry={'parts':[{'id':'part','name':'Test part','process':'print','mass_kg':.5,
        'mass_quality':'assumed','note':'test','file':'cad/part.stl'}],
        'mass_properties':{'allowances':[{'id':'installation','name':'Unresolved items',
            'mass_kg':.055,'quality':'estimated','note':'not selected'}]},
        'coverage':{'open_items':['Joints unresolved']}}
    write_package(tmp_path,None,SimpleNamespace(id='test-design'),geometry)
    rows=list(csv.DictReader((tmp_path/'bom.csv').open()))
    assert sum(float(r['mass_kg']) for r in rows)==.555
    ast.parse((tmp_path/'regenerate.py').read_text())
    assembly=json.loads((tmp_path/'assembly.json').read_text())
    assert assembly['status']=='UNKNOWN'
    assert all(step['verification_status']=='UNKNOWN' for step in assembly['steps'])
