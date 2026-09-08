"""Manufacturing and assembly outputs owned by the aircraft domain."""
import csv
import json


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
build(parameters,system["scenario"],root/"regenerated",components=system["components"],interfaces=system.get("interfaces",[]))
''')
    sequence=[
        {'title':'Prepare the wing modules','groups':['wing','structure'],'action':'Inspect printed shells and cut spar stock to the recorded lengths. Dry-fit seams and spar alignment before bonding.'},
        {'title':'Assemble the fuselage and tail','groups':['fuselage','tail','structure'],'action':'Dry-fit pod modules, boom and tail. Confirm alignment datums and design incidence.'},
        {'title':'Install propulsion and controls','groups':['power','controls'],'action':'Resolve motor fasteners, control hinges/linkages, servo mounting and wire routing before assembly. These details are open.'},
        {'title':'Place battery and mission payload','groups':['power','payload'],'action':'Use the versioned positions, provide positive retention, then measure the actual installed CG.'},
        {'title':'Measure before release','groups':['wing','tail','fuselage','power','controls','payload'],'action':'Complete structural, propulsion, control/access and manufacturing checks. Flight validation requires physical test evidence.'},
    ]
    installation=geometry.get('installation')
    if installation:
        sequence=[
            {'title':'Inspect and prepare fabricated parts','groups':['wing','fuselage','tail','structure'],
             'action':'Slice the individual shells in their intended print orientation, calibrate foamed-PLA density, and inspect walls. Cut the two spar lengths and boom from the recorded stock dimensions. Dry-fit all parts before bonding.',
             'tools':['Calipers','Square','Fine-tooth composite saw with dust extraction','Slicer'],
             'checks':['Measured stock dimensions','Print coupon density','No cracks or delamination'],'requirement_ids':['print-size','cad-valid']},
            {'title':'Join the pod and fit component supports','groups':['fuselage','structure','power','payload','controls'],
             'action':'Fit the two internal seam collars across pod joints. Bond the pod-conforming tray feet and servo cradles to their mating surfaces. Leave both hatches and the complete wing/saddle assembly off.',
             'tools':['Alignment jig','Compatible adhesive and clamps'],
             'hardware':['Pod seam collars × 2','Slotted battery, payload, ESC and receiver trays','Servo cradles × 4'],
             'checks':['Dry-fit before adhesive','Bond area, adhesive process and cure remain unverified'],'requirement_ids':['assembly','full-structure']},
            {'title':'Install battery, payload, receiver and ESC','groups':['power','payload','controls','fuselage'],
             'action':'Lower each component vertically into its versioned position with wing, spar, saddle and hatches removed. Route 10 mm straps through the tray slots. Keep the propeller off and the battery disconnected during wiring.',
             'tools':['Strap threading tool','Calipers'],
             'hardware':['10 mm hook-and-loop straps, cut to measured route','Soft battery/payload padding'],
             'checks':['Inspect continuous insertion-envelope evidence','Confirm retention and lead clearance physically'],'requirement_ids':['component-fit','component-insertion']},
            {'title':'Fit wing spars and mounting saddle','groups':['wing','structure'],
             'action':'Dry-fit both spar halves into the saddle sockets, then slide the ribbed wing modules over the spars. Align the root and segment seams. The socket geometry defines the fit; it does not prove the center joint load capacity.',
             'tools':['Incidence gauge','Straightedge','Bonding jig'],
             'hardware':['Two cut spar halves','Saddle with center sockets','Wing modules'],
             'checks':['Check tube and socket diameters','Verify dihedral and incidence','Load-test the center joint before flight'],'requirement_ids':['spar','deflection','full-structure']},
            {'title':'Connect controls and the radio system','groups':['controls','tail','power'],
             'action':'Install the four ES08MA II servos and follow the channel schedule. Fit hinges, horns and linkages after checking horn travel and loaded torque. Bind the ER6 to a compatible 2.4 GHz ExpressLRS transmitter; verify control direction and throttle failsafe with the propeller removed.',
             'tools':['Servo tester','Multimeter','Compatible transmitter'],
             'hardware':['ES08MA II × 4','ER6 receiver','Servo extensions; lengths from installed routes'],
             'checks':['Nominal BEC voltage and channel-count evidence','Measure simultaneous servo current','Horns, linkage geometry, failsafe and range check remain open'],'requirement_ids':['control-voltage','control-channels','control-current','assembly']},
            {'title':'Complete propulsion mounting','groups':['power','structure'],
             'action':'Dry-fit the plywood pylon and firewall against the manufacturer mounting drawing. Resolve M3 screw engagement and the shaft adapter against delivered hardware before tightening. Fit the APC propeller last; its marked face and rotation must produce forward aircraft thrust in this pusher installation.',
             'tools':['Hex drivers','Calipers','Propeller balancer','Thrust/current test stand'],
             'hardware':['EMAX GT2215','Four M3 mounting screws: engagement pending','APC LP08040E and adapter rings'],
             'checks':['Full rigid propeller swept-envelope evidence','Verify screw engagement, adapter retention, thrust direction and current physically'],'requirement_ids':['prop-clearance','endurance','full-structure']},
            {'title':'Retain covers and measure the installed aircraft','groups':['fuselage','power','payload','wing','tail'],
             'action':'Fit and retain the access covers, then weigh the complete aircraft and measure CG with the actual payload. Compare measurements against this design before re-running verification. Remove any temporary assembly fixtures.',
             'tools':['Scale','CG balance fixture','Calipers'],
             'hardware':['Cover retention tape or straps; adhesion/load test pending'],
             'checks':['Actual mass and CG','Control travel, wire chafe and secure retention'],'requirement_ids':['mass','assembly']},
            {'title':'Close the remaining release evidence','groups':['wing','tail','fuselage','power','controls','payload'],
             'action':'Complete joint/control load tests, propulsion/endurance measurements, print-process validation and radio checks. Physical flight remains UNKNOWN until measured. A CAD or clearance PASS alone does not release this aircraft.',
             'tools':['Wing load-test rig','Power analyzer','Flight-test instrumentation'],
             'checks':['Resolve every mandatory FAIL/UNKNOWN before the corresponding release'],'requirement_ids':['full-structure','control-current','endurance','flight']},
        ]
    verification_path=folder/'verification.json'
    verification=json.loads(verification_path.read_text()) if verification_path.exists() else {}
    evaluations={e['requirement_id']:e for e in verification.get('evaluations',[])}
    for index,step in enumerate(sequence):
        step['id']=f'assembly-{index+1}'
        step['depends_on']=[f'assembly-{index}'] if index else []
        step['part_ids']=[p['id'] for p in geometry['parts'] if p.get('group') in step['groups']]
        step['verification_status']='UNKNOWN'  # full step includes unmodeled assembly actions
        step['evidence_checks']=[{'requirement_id':id,**evaluations.get(id,{'status':'UNKNOWN','evidence_ids':[]})} for id in step.get('requirement_ids',[])]
    if installation:
        write_json(folder/'connection-schedule.json',{'design_id':design.id,'status':'UNKNOWN',
            'channels':installation['control_mapping'],'power':'3S battery → ESC; ESC 5 V BEC → receiver bus → four servos',
            'open_items':['Battery/ESC connector termination','Servo stall/transient current','Wire gauges, lengths and routing','Failsafe and range validation']})
        write_json(folder/'installation-checks.json',geometry.get('installation_checks',{}))

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
    if installation:
        notes += "\n\n## Installation revision\n\n" + installation['revision'] + "\n\nThe assembly.json steps contain versioned parts, tools, installation order and links to evaluated requirements. Slotted trays, pod seam collars and spar sockets are actual CAD parts. Their presence does not validate joints or retention loads. See installation-checks.json for exact checked collision pairs and the declared continuous insertion envelopes. connection-schedule.json records the five control channels and remaining electrical integration work.\n"
    (folder/'FABRICATION.md').write_text(notes)
    return {'assembly_file':f'{design.id}/assembly.json'}
