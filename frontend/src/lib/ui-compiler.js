/**
 * Клиентский компилятор: рекурсивно обходит JSON-дерево UIElement[]
 * и генерирует чистый production-ready код React/Next.js компонента с Tailwind.
 * @typedef {import('../types/ui-builder').UIElement} UIElement
 */

const esc = (s) => String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const escJsx = (s) => String(s == null ? "" : s).replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\n/g, " ");

const TAG = { container: "div", button: "button", text: "p", image: "img", input: "input" };

function renderElement(el, depth) {
  const pad = "  ".repeat(depth);
  const cls = (el.props && el.props.className) || "";
  const tag = TAG[el.type] || "div";
  const cn = cls ? ` className="${escJsx(cls)}"` : "";

  if (el.type === "image") {
    const src = (el.props && el.props.src) || "https://placehold.co/600x400";
    return `${pad}<img${cn} src="${escJsx(src)}" alt="${escJsx(el.name || "image")}" />`;
  }
  if (el.type === "input") {
    const ph = (el.props && el.props.placeholder) || "";
    return `${pad}<input${cn} type="text" placeholder="${escJsx(ph)}" />`;
  }
  if (el.type === "button") {
    const txt = (el.props && el.props.text) || el.name || "Button";
    return `${pad}<button${cn} type="button">${esc(txt)}</button>`;
  }
  if (el.type === "text") {
    const txt = (el.props && el.props.text) || el.name || "";
    return `${pad}<p${cn}>${esc(txt)}</p>`;
  }
  // container
  const kids = Array.isArray(el.children) ? el.children : [];
  if (!kids.length) return `${pad}<div${cn} />`;
  const inner = kids.map((k) => renderElement(k, depth + 1)).join("\n");
  return `${pad}<div${cn}>\n${inner}\n${pad}</div>`;
}

function renderHtmlEl(el) {
  const cls = (el.props && el.props.className) || "";
  const cn = cls ? ` class="${esc(cls)}"` : "";
  const did = ` data-id="${esc(el.id)}"`;
  if (el.type === "image") {
    const src = (el.props && el.props.src) || "https://placehold.co/600x400";
    return `<img${did}${cn} src="${esc(src)}" alt="${esc(el.name || "image")}" />`;
  }
  if (el.type === "input") {
    const ph = (el.props && el.props.placeholder) || "";
    return `<input${did}${cn} type="text" placeholder="${esc(ph)}" />`;
  }
  if (el.type === "button") {
    const txt = (el.props && el.props.text) || el.name || "Button";
    return `<button${did}${cn} type="button">${esc(txt)}</button>`;
  }
  if (el.type === "text") {
    const txt = (el.props && el.props.text) || el.name || "";
    return `<p${did}${cn}>${esc(txt)}</p>`;
  }
  const kids = Array.isArray(el.children) ? el.children : [];
  const inner = kids.map(renderHtmlEl).join("");
  return `<div${did}${cn}>${inner}</div>`;
}

/**
 * Рендерит дерево в HTML-строку с data-id для превью.
 * @param {UIElement[]} elements
 * @returns {string}
 */
export function renderToHtml(elements) {
  return (Array.isArray(elements) ? elements : []).map(renderHtmlEl).join("");
}

/**
 * Компилирует дерево элементов в строковый код компонента.
 * @param {UIElement[]} elements
 * @param {string} [componentName]
 * @returns {string}
 */
export function compileToNextJS(elements, componentName = "GeneratedSection") {
  const body = (Array.isArray(elements) ? elements : []).map((e) => renderElement(e, 2)).join("\n");
  return `"use client";

import React from "react";

export default function ${componentName}() {
  return (
    <section className="w-full">
${body}
    </section>
  );
}
`;
}
