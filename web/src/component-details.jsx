import React from "react";
import { ArrowUpRight, Download, ExternalLink, X } from "lucide-react";

// Storefront navigation only. Engineering properties come from the frozen CAD catalog.
const stores = {
  "EMAX:0102003010": {
    name: "EMAX",
    url: "https://shop.emaxmodel.com/collections/hot-products/products/emax-es08ma-ii-12g-mini-metal-gear-analog-servo-for-rc-model-robot-pwm-servo",
  },
  "RadioMaster:HP0157.RX-ER6": {
    name: "RadioMaster",
    url: "https://radiomasterrc.com/products/er6-2-4ghz-elrs-pwm-receiver",
  },
  "APC:LP08040E": { name: "APC", url: "https://www.apcprop.com/product/8x4e/" },
  "Easy Composites:CFT-WF-10-8-1": {
    name: "Easy Composites",
    url: "https://www.easycomposites.co.uk/10mm-8mm-woven-finish-carbon-fibre-tube",
  },
  "Easy Composites:CFT-WF-12-10-1": {
    name: "Easy Composites",
    url: "https://www.easycomposites.co.uk/12mm-10mm-woven-finish-carbon-fibre-tube",
  },
  "EMAX:EMX-MT-0409": {
    name: "EMAX",
    url: "https://emax-usa.com/collections/diy/products/emx-mt-0409-gt2215-1180kv",
  },
  "Tattu:TAA13003S75X6": {
    name: "Tattu",
    url: "https://www.tattuworld.com/products/tattu-classic-1300mah-3s1p-11-1v-75c-fpv-lipo-battery.html",
  },
  "Hobbywing:30205200": {
    name: "Hobbywing",
    url: "https://www.hobbywingdirect.com/products/skywalker-esc-20a",
  },
};
const labels = {
  min_voltage_v: "Minimum voltage",
  max_voltage_v: "Maximum voltage",
  stall_torque_nm: "Stall torque",
  torque_test_voltage_v: "Torque test voltage",
  channels: "PWM outputs",
  mount_spacing_m: "Mount spacing",
  linear_mass_kg_m: "Mass per metre",
  axial_modulus_pa: "Axial modulus",
  kv: "Motor KV",
  mass_kg: "Component mass",
  cells: "Cell count",
  capacity_ah: "Capacity",
  nominal_v: "Nominal voltage",
  current_a: "Continuous current",
  min_cells: "Minimum cells",
  max_cells: "Maximum cells",
  bec_v: "BEC voltage",
  bec_a: "BEC current",
  quantity: "System quantity",
  length_m: "Length",
  width_m: "Width",
  height_m: "Height",
  diameter_m: "Diameter",
  body_length_m: "Body length",
  shaft_diameter_m: "Shaft diameter",
  mount_horizontal_m: "Mount spacing · H",
  mount_vertical_m: "Mount spacing · V",
  mount_thread: "Mount thread",
  connector: "Connector",
};
const human = (value) => value?.replaceAll("_", " ").replaceAll("-", " ") || "";
const numeric = (value) =>
  Number.isFinite(value)
    ? Number(value.toFixed(2)).toLocaleString("en-US")
    : "—";
function formatProperty({ value, unit }) {
  if (typeof value !== "number")
    return `${value ?? "Unknown"}${unit && unit !== "1" ? ` ${unit}` : ""}`;
  if (unit === "m") return `${numeric(value * 1000)} mm`;
  if (unit === "kg") return `${numeric(value * 1000)} g`;
  if (unit === "Pa") return `${numeric(value / 1e9)} GPa`;
  if (unit === "kg/m") return `${numeric(value * 1000)} g/m`;
  if (unit === "Ah") return `${numeric(value * 1000)} mAh`;
  return `${numeric(value)}${unit && unit !== "1" ? ` ${unit}` : ""}`;
}
function safeUrl(value) {
  try {
    const parsed = new URL(value);
    return ["https:", "http:"].includes(parsed.protocol) ? parsed.href : null;
  } catch {
    return null;
  }
}
function sourceLabel(source) {
  const parsed = new URL(source);
  if (/\.pdf$/i.test(parsed.pathname)) return "Datasheet · PDF";
  if (/\.(jpg|png|webp)$/i.test(parsed.pathname))
    return "Manufacturer drawing / table";
  return parsed.hostname.replace(/^www\./, "");
}
export default function ComponentDetails({ part, downloadUrl, onClose }) {
  const component = part.component;
  const properties = Object.entries(component?.properties || {});
  const sources = [
    ...new Set(properties.map(([, p]) => safeUrl(p.source)).filter(Boolean)),
  ];
  const store = stores[`${component?.manufacturer}:${component?.part_number}`];
  return (
    <div className="component-details">
      <div className="panel-heading">
        <span>PART DETAILS</span>
        <button onClick={onClose} aria-label="Close part details">
          <X size={15} />
        </button>
      </div>
      <span className="tiny-label">
        {human(part.group)} · {human(part.process)}
      </span>
      <h2>{part.name}</h2>
      {component && (
        <div className="component-identity">
          <strong>{component.name}</strong>
          <span>{component.manufacturer || "Manufacturer pending"}</span>
          <code>{component.part_number || "Part selection pending"}</code>
        </div>
      )}
      {store ? (
        <a
          className="component-buy"
          href={store.url}
          target="_blank"
          rel="noopener noreferrer"
        >
          View / buy at {store.name}
          <ArrowUpRight size={15} />
        </a>
      ) : (
        part.process === "purchase" && (
          <p className="component-pending">
            {component?.part_number
              ? "Purchase link not recorded."
              : "Exact part selection UNKNOWN. Purchase link pending."}
          </p>
        )
      )}
      {store && (
        <p className="tiny muted">
          Price and availability on the supplier’s site.
        </p>
      )}
      {properties.length > 0 && (
        <section className="component-section">
          <h3>Recorded specifications</h3>
          <dl className="component-specs">
            {properties.map(([key, property]) => {
              const link = safeUrl(property.source);
              return (
                <div key={key}>
                  <dt>{labels[key] || human(key)}</dt>
                  <dd>
                    <b>{formatProperty(property)}</b>
                    <span className="property-quality">
                      {human(property.quality) || "unknown"}
                      {link && (
                        <a
                          href={link}
                          target="_blank"
                          rel="noopener noreferrer"
                          aria-label={`Source for ${labels[key] || human(key)}`}
                          title="Open recorded source"
                        >
                          <ExternalLink size={10} />
                        </a>
                      )}
                    </span>
                    {!link && property.source && (
                      <small>{property.source}</small>
                    )}
                  </dd>
                </div>
              );
            })}
          </dl>
          <p className="tiny muted">
            From this design’s frozen catalog. Sourced values are not
            installed-system verification.
          </p>
        </section>
      )}
      <section className="component-section">
        <h3>{component ? "CAD envelope" : "Fabrication details"}</h3>
        <dl className="component-specs">
          <div>
            <dt>Modeled mass</dt>
            <dd>
              <b>{numeric(part.mass_kg * 1000)} g</b>
              <small>{human(part.mass_quality)}</small>
            </dd>
          </div>
          <div>
            <dt>Bounds</dt>
            <dd>
              <b>
                {part.dimensions_m?.map((v) => numeric(v * 1000)).join(" × ")}{" "}
                mm
              </b>
            </dd>
          </div>
          {Object.entries(part.stock || {}).map(([key, value]) => (
            <div key={key}>
              <dt>{human(key.replace(/_mm$/, ""))}</dt>
              <dd>
                <b>
                  {typeof value === "number" ? numeric(value) : value}
                  {key.endsWith("_mm") ? " mm" : ""}
                </b>
              </dd>
            </div>
          ))}
        </dl>
        {part.note && <p className="small-copy">{part.note}</p>}
        {part.file && (
          <a className="component-buy secondary" href={downloadUrl} download>
            Download part {part.file.endsWith(".step") ? "STEP" : "STL"}
            <Download size={14} />
          </a>
        )}
      </section>
      {sources.length > 0 && (
        <details className="component-sources">
          <summary>Sources & drawings ({sources.length})</summary>
          {sources.map((source) => (
            <a
              key={source}
              href={source}
              target="_blank"
              rel="noopener noreferrer"
            >
              {sourceLabel(source)}
              <ExternalLink size={11} />
            </a>
          ))}
        </details>
      )}
      {component?.revision && (
        <p className="tiny muted component-revision">
          Catalog revision · {component.revision}
        </p>
      )}
    </div>
  );
}
