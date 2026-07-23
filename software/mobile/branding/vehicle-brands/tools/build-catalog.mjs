import fs from "node:fs";
import path from "node:path";

const [simpleIconsRoot, outputRoot] = process.argv.slice(2);
if (!simpleIconsRoot || !outputRoot) {
  throw new Error("usage: node build-catalog.mjs <simple-icons package> <output>");
}

const sourceCatalog = JSON.parse(
  fs.readFileSync(path.join(outputRoot, "sources.json"), "utf8"),
);
const simpleMetadata = JSON.parse(
  fs.readFileSync(path.join(simpleIconsRoot, "data/simple-icons.json"), "utf8"),
);
const metadataBySlug = new Map(simpleMetadata.map((item) => [item.slug, item]));

function withColor(svg, color) {
  return svg.replace(/<svg\b([^>]*)>/, (opening) =>
    opening.replace(/>$/, ` fill="${color}">`),
  );
}

function withOverrideColor(svg, color) {
  const style = `<style>
    path:not([fill="none"]), polygon:not([fill="none"]),
    rect:not([fill="none"]), circle:not([fill="none"]),
    ellipse:not([fill="none"]) { fill: ${color} !important; }
    [stroke]:not([stroke="none"]) { stroke: ${color} !important; }
  </style>`;
  return svg.replace(/<svg\b([^>]*)>/, (opening) =>
    `${opening.replace(/>$/, ` fill="${color}">`)}${style}`,
  );
}

function replaceSourceColors(svg, sourceColors, color) {
  return (sourceColors ?? []).reduce((result, sourceColor) => {
    const escaped = sourceColor.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    return result.replace(new RegExp(escaped, "gi"), color);
  }, svg);
}

function makeVariant(svg, brand, color) {
  return withOverrideColor(
    replaceSourceColors(svg, brand.recolorFrom, color),
    color,
  );
}

for (const brand of sourceCatalog.brands) {
  const brandDirectory = path.join(outputRoot, "brands", brand.id);
  fs.mkdirSync(brandDirectory, { recursive: true });

  if (brand.simpleIconSlug) {
    const iconPath = path.join(
      simpleIconsRoot,
      "icons",
      `${brand.simpleIconSlug}.svg`,
    );
    if (!fs.existsSync(iconPath)) {
      throw new Error(`${brand.id}: missing Simple Icons slug ${brand.simpleIconSlug}`);
    }
    const svg = fs.readFileSync(iconPath, "utf8");
    fs.writeFileSync(path.join(brandDirectory, "logo-source.svg"), svg);
    fs.writeFileSync(
      path.join(brandDirectory, "logo-on-dark.svg"),
      withColor(svg, "#FFFFFF"),
    );
    fs.writeFileSync(
      path.join(brandDirectory, "logo-on-light.svg"),
      withColor(svg, "#000000"),
    );
    fs.writeFileSync(
      path.join(brandDirectory, "logo-accent.svg"),
      withColor(svg, brand.accentColor),
    );
    const metadata = metadataBySlug.get(brand.simpleIconSlug);
    brand.simpleIcons = {
      slug: brand.simpleIconSlug,
      title: metadata?.title ?? brand.name,
      source: metadata?.source ?? brand.source,
      guidelines: metadata?.guidelines ?? null,
      license: metadata?.license ?? null,
    };
  }

  const normalizedSource = path.join(brandDirectory, "logo-source.svg");
  if (fs.existsSync(normalizedSource)) {
    const svg = fs.readFileSync(normalizedSource, "utf8");
    fs.writeFileSync(
      path.join(brandDirectory, "logo-on-dark.svg"),
      makeVariant(svg, brand, "#FFFFFF"),
    );
    fs.writeFileSync(
      path.join(brandDirectory, "logo-on-light.svg"),
      makeVariant(svg, brand, "#000000"),
    );
    fs.writeFileSync(
      path.join(brandDirectory, "logo-accent.svg"),
      makeVariant(svg, brand, brand.accentColor),
    );
  }

  fs.writeFileSync(
    path.join(brandDirectory, "brand.json"),
    `${JSON.stringify(brand, null, 2)}\n`,
  );
}

fs.writeFileSync(
  path.join(outputRoot, "vehicle-brands-v1.json"),
  `${JSON.stringify(sourceCatalog, null, 2)}\n`,
);
