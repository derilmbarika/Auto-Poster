"use client";

import { gsap } from "@/lib/gsap";

/** Shared easing + timing tokens so motion feels consistent across the site. */
export const EASE = {
  out: "power3.out",
  inOut: "power2.inOut",
  expo: "expo.out",
} as const;

/**
 * Wraps each word or character of an element in inline-block spans so they can
 * be animated individually. Returns the created spans. Idempotent-ish: it reads
 * textContent, so call once per element. A lightweight stand-in for GSAP's
 * SplitText that needs no Club plugin.
 */
export function splitText(
  el: HTMLElement,
  by: "word" | "char" = "word"
): HTMLElement[] {
  const text = el.textContent ?? "";
  el.textContent = "";
  el.style.setProperty("--split-overflow", "hidden");

  const units = by === "word" ? text.split(/(\s+)/) : Array.from(text);
  const spans: HTMLElement[] = [];

  for (const unit of units) {
    if (by === "word" && /^\s+$/.test(unit)) {
      el.appendChild(document.createTextNode(unit));
      continue;
    }
    // Outer mask clips the inner span as it slides up — a clean reveal edge.
    const mask = document.createElement("span");
    mask.style.display = "inline-block";
    mask.style.overflow = "hidden";
    mask.style.verticalAlign = "top";

    const inner = document.createElement("span");
    inner.style.display = "inline-block";
    inner.textContent = unit;
    inner.style.willChange = "transform";

    mask.appendChild(inner);
    el.appendChild(mask);
    spans.push(inner);
  }
  return spans;
}

/** Fade + rise reveal, triggered when the element scrolls into view. */
export function fadeUp(
  targets: gsap.TweenTarget,
  trigger: Element,
  opts: { y?: number; duration?: number; stagger?: number; delay?: number } = {}
) {
  const { y = 40, duration = 0.9, stagger = 0, delay = 0 } = opts;
  return gsap.from(targets, {
    y,
    autoAlpha: 0,
    duration,
    delay,
    stagger,
    ease: EASE.out,
    scrollTrigger: { trigger, start: "top 80%", once: true },
  });
}

/** Masked text reveal: split spans slide up from behind their clip mask. */
export function textReveal(
  el: HTMLElement,
  by: "word" | "char" = "word",
  opts: { stagger?: number; duration?: number; start?: string } = {}
) {
  const { stagger = by === "char" ? 0.02 : 0.08, duration = 0.9, start = "top 85%" } =
    opts;
  const spans = splitText(el, by);
  return gsap.from(spans, {
    yPercent: 120,
    duration,
    ease: EASE.expo,
    stagger,
    scrollTrigger: { trigger: el, start, once: true },
  });
}

/** Scrubbed parallax: moves the target as the section travels the viewport. */
export function parallax(
  target: gsap.TweenTarget,
  trigger: Element,
  opts: { from?: number; to?: number } = {}
) {
  const { from = -12, to = 12 } = opts;
  return gsap.fromTo(
    target,
    { yPercent: from },
    {
      yPercent: to,
      ease: "none",
      scrollTrigger: { trigger, start: "top bottom", end: "bottom top", scrub: true },
    }
  );
}
