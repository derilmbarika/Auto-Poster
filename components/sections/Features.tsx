"use client";

import { useRef } from "react";
import { gsap, useGSAP } from "@/lib/gsap";
import { fadeUp, textReveal } from "@/lib/animations";

const FEATURES = [
  { n: "01", t: "Smooth scroll", d: "Lenis virtual scroll driven by the GSAP ticker — one render loop." },
  { n: "02", t: "ScrollTrigger", d: "Scrubbed, pinned, and once-triggered reveals, all kept in sync." },
  { n: "03", t: "Reduced motion", d: "Every animation gated behind matchMedia; content never hidden." },
  { n: "04", t: "Auto cleanup", d: "useGSAP reverts timelines and triggers on unmount. No leaks." },
];

export default function Features() {
  const root = useRef<HTMLElement>(null);

  useGSAP(
    () => {
      const mm = gsap.matchMedia();
      mm.add("(prefers-reduced-motion: no-preference)", () => {
        const heading = root.current!.querySelector<HTMLElement>(".features__h");
        textReveal(heading!, "word");
        // Staggered card reveal.
        fadeUp(".feature", root.current!, { y: 50, stagger: 0.1, duration: 0.8 });
      });
    },
    { scope: root }
  );

  return (
    <section ref={root} className="section container" aria-labelledby="features-h">
      <p className="eyebrow">The stack</p>
      <h2 id="features-h" className="features__h display" style={{ fontSize: "clamp(2rem,5vw,3.8rem)", marginTop: "1rem" }}>
        Production-ready, not a demo.
      </h2>
      <div className="features__grid">
        {FEATURES.map((f) => (
          <article className="feature reveal-hidden" key={f.n}>
            <span className="feature__num">{f.n}</span>
            <div>
              <h3>{f.t}</h3>
              <p>{f.d}</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
