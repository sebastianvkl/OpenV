import test from 'node:test';
import assert from 'node:assert/strict';
import {attachStepMeshes,stepPartNames} from './step-model.mjs';
const positions=[0,0,0,.02,0,0,0,.02,0],indices=[0,1,2];
const geometry={parts:[{id:'servo-1',component:{part_number:'exact-servo'},mesh:{positions,indices}}]};
const mesh={name:'servo-1',positions,indices,faceCount:1};
test('Assembly instance names identify generic SOLID meshes; ambiguous instances are rejected',()=>{
 const root={name:'aircraft',meshes:[],children:[{name:'battery',meshes:[0]},{name:'servo-1',meshes:[1]}]};
 assert.deepEqual(stepPartNames(root,2),['battery','servo-1']);
 assert.throws(()=>stepPartNames({...root,children:[...root.children,{name:'duplicate',meshes:[1]}]},2),/Ambiguous/);
 assert.throws(()=>stepPartNames(root,3),/Missing/);
});
test('STEP geometry retains frozen component identity without making a verdict',()=>{
 const r=attachStepMeshes(geometry,[mesh]);assert.equal(r.geometry.parts[0].component.part_number,'exact-servo');assert.equal(r.triangles,1);assert.equal(r.faces,1);assert.equal(r.status,undefined);
});
test('Missing, duplicate or wrong STEP identities cannot borrow component metadata',()=>{
 assert.throws(()=>attachStepMeshes(geometry,[]),/meshes/);
 assert.throws(()=>attachStepMeshes(geometry,[{...mesh,name:'battery'}]),/identity/);
 assert.throws(()=>attachStepMeshes({parts:[...geometry.parts,...geometry.parts]},[mesh,mesh]),/Ambiguous/);
});
test('Wrong scale, misplaced geometry, invalid indices and nonfinite coordinates fail visibly',()=>{
 for(const positions of [[0,0,0,20,0,0,0,20,0],[1,0,0,1.02,0,0,1,.02,0],[NaN,0,0,.02,0,0,0,.02,0]])assert.throws(()=>attachStepMeshes(geometry,[{...mesh,positions}]));
 assert.throws(()=>attachStepMeshes(geometry,[{...mesh,indices:[0,1,99]}]),/index/);
});
