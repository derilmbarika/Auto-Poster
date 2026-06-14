"use client";

import { useRef } from "react";
import { gsap, useGSAP } from "@/lib/gsap";
import { textReveal } from "@/lib/animations";

export default function SvgPath() {
  const root = useRef<HTMLElement>(null);

  useGSAP(
    () => {
      const mm = gsap.matchMedia();
      mm.add("(prefers-reduced-motion: no-preference)", () => {
        const heading = root.current!.querySelector<HTMLElement>(".path__h");
        textReveal(heading!, "word");

        // Draw the stroke by scrubbing dashoffset — no DrawSVG plugin needed.
        const path = root.current!.querySelector<SVGPathElement>(".path__line")!;
        const len = path.getTotalLength();
        gsap.set(path, { strokeDasharray: len, strokeDashoffset: len });
        gsap.to(path, {
          strokeDashoffset: 0,
          ease: "none",
          scrollTrigger: { trigger: root.current, start: "top 70%", end: "bottom 60%", scrub: true },
        });
      });
    },
    { scope: root }
  );

  return (
    <section ref={root} className="section container path" aria-labelledby="path-h">
      <p className="eyebrow" style={{ display: "inline-block" }}>
        SVG
      </p>
      <h2 id="path-h" className="path__h display" style={{ fontSize: "clamp(2rem,5vw,3.8rem)", marginTop: "1rem" }}>
        Lines that draw on scroll.
      </h2>
      <svg viewBox="0 0 720 220" role="img" aria-label="An animated flowing line">
        <path
          className="path__line"
          d="M10 170 C 130 30, 230 30, 350 110 S 590 210, 710 60"
        />
      </svg>
    </section>
  );
}
