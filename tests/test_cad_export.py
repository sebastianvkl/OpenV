from build123d import Box,Compound,Location,export_step,import_step

from openv.cad import roundtrip_checks,cad_output


def test_step_roundtrip_checks_identity_position_and_scale_not_just_volume(tmp_path):
    shape=Box(10,20,30);shape.label='bracket'
    path=tmp_path/'bracket.step'
    export_step(Compound(children=[shape]),str(path))
    parts=[{'id':'bracket','centroid_m':[0,0,0],'dimensions_m':[.01,.02,.03]}]
    good=roundtrip_checks(parts,import_step(str(path)))
    assert good['step_part_id_mismatches']==0
    assert good['step_centroid_max_error_m']<1e-8
    assert good['step_bounds_max_error_m']<1e-8
    moved=shape.moved(Location((100,0,0)));moved.label='bracket'
    wrong=roundtrip_checks(parts,Compound(children=[moved]))
    checks={'step_volume_relative_error':0,'max_print_dimension_m':.03,'invalid_solids':0,**wrong}
    assert wrong['step_centroid_max_error_m']>.09
    assert not cad_output({'cad_checks':checks}).metrics['invalid_solids'].admissible
    renamed=shape.moved(Location((0,0,0)));renamed.label='different-part'
    assert roundtrip_checks(parts,Compound(children=[renamed]))['step_part_id_mismatches']>0
