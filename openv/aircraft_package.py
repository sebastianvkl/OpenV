"""Manufacturing and assembly outputs owned by the aircraft domain."""
import csv


def write_package(folder,hardware,design,geometry):
    from openv.pipeline import write_json
    bom=[]
    for part in geometry['parts']:
        component=part.get('component',{})
        sources=sorted({p['source'] for p in component.get('properties',{}).values() if p.get('source')})
        bom.append({**{k:part[k] for k in ('id','name','process','mass_kg','mass_quality','note')},
            'quantity':1,'manufacturer':component.get('manufacturer',''),
            'part_number':component.get('part_number',''),'sources':' | '.join(sources),
            'cad_file':part.get('file') or '', 'fabrication':str(part.get('stock',{}))})
    for item in geometry['mass_properties']['allowances']:
        bom.append({'id':item['id'],'name':item['name'],'process':'unresolved installation items',
            'mass_kg':item['mass_kg'],'mass_quality':item['quality'],'note':item['note'],'quantity':1})
    with (folder/'bom.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(bom[0]));writer.writeheader();writer.writerows(bom)
    write_json(folder/'fabrication-parts.json',{'units':'mm','status':'UNKNOWN',
        'parts':[{k:v for k,v in p.items() if k!='mesh'} for p in geometry['parts'] if p['process'] not in ('purchase','provided')]})
    (folder/'regenerate.py').write_text('''"""Install ./source, then regenerate this exact candidate geometry."""
import json
from pathlib import Path
from openv.cad import build
root=Path(__file__).resolve().parent
parameters=json.loads((root/"design-parameters.json").read_text())
system=json.loads((root/"system.json").read_text())
build(parameters,system["scenario"],root/"regenerated",components=system["components"])
''')
    sequence=[
        {'title':'Prepare the wing modules','groups':['wing','structure'],'action':'Inspect printed shells and cut spar stock to the recorded lengths. Dry-fit seams and spar alignment before bonding.'},
        {'title':'Assemble the fuselage and tail','groups':['fuselage','tail','structure'],'action':'Dry-fit pod modules, boom and tail. Confirm alignment datums and design incidence.'},
        {'title':'Install propulsion and controls','groups':['power','controls'],'action':'Resolve motor fasteners, control hinges/linkages, servo mounting and wire routing before assembly. These details are open.'},
        {'title':'Place battery and mission payload','groups':['power','payload'],'action':'Use the versioned positions, provide positive retention, then measure the actual installed CG.'},
        {'title':'Measure before release','groups':['wing','tail','fuselage','power','controls','payload'],'action':'Complete structural, propulsion, control/access and manufacturing checks. Flight validation requires physical test evidence.'},
    ]
    for step in sequence:step['verification_status']='UNKNOWN'
    write_json(folder/'assembly.json',{'design_id':design.id,'status':'UNKNOWN','steps':sequence})
    notes='''# Fabrication candidate — release blocked

STEP/STL and stock dimensions are millimeters. Web mesh, bounding dimensions
and canonical geometry use meters. All assembly files retain their global
position; orient each part deliberately in CAM or the slicer.

Printed shells use an assumed foamed-PLA density. Calibrate material/process
coupons and slicing before manufacturing. No G-code is supplied. Inspect seams,
wall thickness, supports and orientation before printing. Carbon tube layup and
joints are unvalidated. Purchased-part meshes are envelopes, not manufacturing
models. Individual STEP files are supplied for cut-stock and plywood parts;
stock dimensions are in fabrication-parts.json. The frozen component catalog
identifies whether the motor mounting pattern uses a vendor drawing or a legacy
estimate. Confirm the delivered variant, fastener engagement and mounting loads
before cutting; a sourced hole pattern alone does not verify the installation.

The BOM includes the separate 55 g installation allowance in the mass model.
This is an unresolved collection of parts, not a purchasing specification.

## Open design items

'''+ '\n'.join(f'- {item}' for item in geometry['coverage']['open_items'])
    (folder/'FABRICATION.md').write_text(notes)
    return {'assembly_file':f'{design.id}/assembly.json'}
