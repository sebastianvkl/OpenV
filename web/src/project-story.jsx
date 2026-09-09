import React from "react";
import { ArrowUpRight, ArrowRight } from "lucide-react";
const repair = "https://openv-kohl.vercel.app/?run=run-dcef3705d89d&view=fit";
const candidate = "https://openv-kohl.vercel.app/?run=run-365c68904f40";
export default function ProjectStory() {
  return <section className="project-story" aria-label="About the OpenV pipeline">
    <div className="story-heading">
      <span className="story-kicker">01 / THE ENGINEERING LOOP</span>
      <h2>A beautiful design<br />still has to earn its evidence.</h2>
      <p>Describe the mission. Let Astra propose a design. Give independent engineering tools the final say—and send the failures back for another iteration.</p>
    </div>
    <div className="story-loop" aria-label="Intent, requirements, design, verify, redesign, verify">
      {["Intent", "Requirements", "Design", "Verify", "Redesign", "Verify again"].map((label, i) => <React.Fragment key={label}>
        {i > 0 && <ArrowRight size={16} aria-hidden="true" />}
        <span className={i === 3 || i === 5 ? "loop-verifier" : ""}><small>0{i + 1}</small>{label}</span>
      </React.Fragment>)}
    </div>
    <article className="story-experiment">
      <div>
        <span className="story-kicker">RECORDED ASTRA EXPERIMENT / ALBATROSS 01</span>
        <h3>3.6 mm.<br /><em>A very real difference.</em></h3>
        <p>The first candidate placed its battery inside two servo mounts. Solid geometry checks found the overlap. Astra moved the battery forward; seven dependent evidence records were invalidated before fresh verification.</p>
        <a href={repair}>Follow the actual repair <ArrowUpRight size={17} /></a>
      </div>
      <div className="story-proof">
        <a className="proof-version" href={`${repair}&version=design-7e5e14a82ca4`}>
          <span>V01 / INITIAL HYPOTHESIS</span><b className="proof-fail">2 collisions</b><p>Battery intersects both tail-servo mounts.</p><small>10.45 mm³ overlap per mount <ArrowUpRight size={14} /></small>
        </a>
        <div className="proof-change"><span>Battery x: 411.6 → 408.0 mm</span><ArrowRight size={17} /></div>
        <a className="proof-version" href={repair}>
          <span>V02 / EXTERNAL RE-VERIFICATION</span><b>0 collisions</b><p>The scoped component-fit and insertion checks pass.</p><small>16 modeled PASS · 8 UNKNOWN <ArrowUpRight size={14} /></small>
        </a>
        <p className="proof-scope">Recorded run: run-dcef3705d89d. Manufacturing and physical flight release remain open.</p>
      </div>
    </article>
    <div className="story-heading story-gallery-heading"><span className="story-kicker">02 / INSPECT EVERY LAYER</span><h2>From engineering state<br />to something you can explore.</h2></div>
    <div className="story-gallery">
      <a href={`${candidate}&view=flight`}><div className="story-image"><img src="/images/flight.webp" alt="OpenV playing an AeroSandbox-based aircraft response in a 3D landscape" loading="lazy" width="1600" height="1000" /></div><span>01 / SIMULATION <ArrowUpRight size={17} /></span><h3>See the response.</h3><p>Explore computed flight, airflow and load cases. Inspect the assumptions behind the animation.</p></a>
      <a href={`${candidate}&view=assemble`}><div className="story-image"><img src="/images/assembly.webp" alt="The actual 45-part STEP aircraft assembly shown in OpenV" loading="lazy" width="1600" height="1000" /></div><span>02 / CAD & ASSEMBLY <ArrowUpRight size={17} /></span><h3>Get inside the design.</h3><p>Read the real STEP, isolate components, inspect dimensions and download the matching candidate package.</p></a>
    </div>
    <div className="story-stack">
      <div><span className="story-kicker">03 / AN OPEN PIPELINE</span><h2>The tools can change.<br />The evidence rule stays.</h2><p>One working aircraft domain today. Explicit adapters and verification contracts make the pipeline a starting point for other hardware systems.</p></div>
      <dl>{[["Astra", "Requirements & engineering proposals"], ["Dalus · MCP", "Persistent engineering record & traceability"], ["build123d · OpenCascade", "Derived CAD & solid geometry checks"], ["AeroSandbox · SciPy", "Aircraft analysis & response diagnostics"], ["Three.js", "Interactive inspection & visualization"]].map(([name, role]) => <div key={name}><dt>{name}</dt><dd>{role}</dd></div>)}</dl>
    </div>
    <div className="story-end"><span>ASTRA PROPOSES. TOOLS EXECUTE. EVIDENCE DECIDES.</span><a href="https://github.com/sebastianvkl/OpenV">Build on OpenV <ArrowUpRight size={20} /></a><p>Open source · MIT application code · Explicit PASS / FAIL / UNKNOWN</p></div>
  </section>;
}
