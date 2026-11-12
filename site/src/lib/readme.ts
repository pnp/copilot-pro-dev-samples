import { marked } from "marked";
import sanitizeHtml from "sanitize-html";
import { repositoryUrl } from "./site";

function repositoryTarget(folder: string, target: string, image: boolean): string {
  if (/^(?:[a-z][a-z\d+.-]*:|\/\/|#)/i.test(target)) return target;
  const base = image
    ? `https://raw.githubusercontent.com/pnp/copilot-pro-dev-samples/main/samples/${folder}/`
    : `${repositoryUrl}/blob/main/samples/${folder}/`;
  return new URL(target, base).href;
}

export async function renderReadme(folder: string, markdown: string): Promise<string> {
  const html = await marked.parse(markdown.replace(/^# .+\r?\n/, ""), { gfm: true });
  return sanitizeHtml(html, {
    allowedTags: [...sanitizeHtml.defaults.allowedTags, "img"],
    allowedAttributes: {
      ...sanitizeHtml.defaults.allowedAttributes,
      a: ["href", "title", "target", "rel"],
      img: ["src", "alt", "title", "width", "height", "loading"],
      code: ["class"],
    },
    allowedSchemes: ["http", "https", "mailto"],
    transformTags: {
      a: (_tagName, attributes) => ({
        tagName: "a",
        attribs: {
          ...attributes,
          href: repositoryTarget(folder, attributes.href ?? "", false),
          ...(attributes.href?.startsWith("#") ? {} : { target: "_blank", rel: "noopener noreferrer" }),
        },
      }),
      img: (_tagName, attributes) => ({
        tagName: "img",
        attribs: { ...attributes, src: repositoryTarget(folder, attributes.src ?? "", true), loading: "lazy" },
      }),
    },
    exclusiveFilter: (frame) => frame.tag === "img" &&
      frame.attribs.src?.startsWith("https://m365-visitor-stats.azurewebsites.net/") === true,
  });
}
