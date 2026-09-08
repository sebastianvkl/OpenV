import React, { useEffect, useState } from "react";
// Presentation references from the exact manufacturer's product page. Never verification inputs.
export const componentReferences = {
  "EMAX:0102003010": {
    image:
      "https://shop.emaxmodel.com/cdn/shop/products/img_9303_1024x1024.jpg?v=1598527257",
    source:
      "https://shop.emaxmodel.com/collections/hot-products/products/emax-es08ma-ii-12g-mini-metal-gear-analog-servo-for-rc-model-robot-pwm-servo",
    label: "EMAX ES08MA II",
  },
  "RadioMaster:HP0157.RX-ER6": {
    image: "https://radiomasterrc.com/cdn/shop/files/ER6-1.jpg?v=1750061572",
    source: "https://radiomasterrc.com/products/er6-2-4ghz-elrs-pwm-receiver",
    label: "RadioMaster ER6",
  },
  "EMAX:EMX-MT-0409": {
    image:
      "https://shop.emax-usa.com/cdn/shop/products/emx-mt-0406-2__05089.1484269695.1280.1280.jpgc-2_1024x1024.jpg?v=1590534746",
    source:
      "https://emax-usa.com/collections/diy/products/emx-mt-0409-gt2215-1180kv",
    label: "EMAX GT2215",
  },
  "APC:LP08040E": {
    image: "https://www.apcprop.com/wp-content/uploads/2017/03/LP08040E.jpg",
    source: "https://www.apcprop.com/product/8x4e/",
    label: "APC 8×4E",
  },
};
export function referenceFor(part) {
  return componentReferences[
    `${part.component?.manufacturer}:${part.component?.part_number}`
  ];
}
export function ReferenceImage({ part }) {
  const reference = referenceFor(part),
    [failed, setFailed] = useState(false);
  useEffect(() => setFailed(false), [reference?.image]);
  if (!reference || failed)
    return <span className="reference-missing">CAD envelope</span>;
  return (
    <img
      src={reference.image}
      alt={`${reference.label} manufacturer reference`}
      loading="lazy"
      referrerPolicy="no-referrer"
      onError={() => setFailed(true)}
    />
  );
}
export default function ComponentReference({ part }) {
  const reference = referenceFor(part);
  if (part.process !== "purchase") return null;
  return (
    <section className="component-reference">
      {reference && (
        <a href={reference.source} target="_blank" rel="noreferrer">
          <ReferenceImage part={part} />
          <span>Manufacturer reference photo ↗</span>
        </a>
      )}
      <p className="tiny">
        3D geometry: simplified component envelope. Detailed vendor CAD and
        unmodeled connectors, leads and internals are not included.
      </p>
    </section>
  );
}
