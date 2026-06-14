"use client";

import { useRef } from "react";
import { gsap, useGSAP } from "@/lib/gsap";
import { textReveal, fadeUp, parallax } from "@/lib/animations";

export default function Intro() {
  const root = useRef<HTMLElement>(null);

  useGSAP(
    () => {
      const mm = gsap.matchMedia();
      mm.add("(prefers-reduced-motion: no-preference)", () => {
        const heading = root.current!.querySelector<HTMLElement>(".intro__heading");
        textReveal(heading!, "word");
        fadeUp(".intro__copy", root.current!, { delay: 0.1 });

        // Parallax on the media panel's inner layer for depth.
        parallax(".intro__media-inner", root.current!, { from: -18, to: 18 });
      });
    },
    { scope: root }
  );

  return (
    <section ref={root} className="section container" aria-labelledby="intro-h">
      <div className="intro">
        <div>
          <p className="eyebrow reveal-hidden intro__copy">Philosophy</p>
          <h2 id="intro-h" className="display intro__heading" style={{ fontSize: "clamp(2rem,5vw,3.8rem)", marginTop: "1.25rem" }}>
            Every transition earns its place.
          </h2>
          <p className="lead reveal-hidden intro__copy" style={{ marginTop: "1.75rem" }}>
            We animate only transform and opacity, drive scroll-linked motion off
            a single shared ticker, and clean every timeline up on unmount. The
            result is interaction that feels inevitable — never busy.
          </p>
        </div>
        <div className="intro__media" aria-hidden>
          <div className="intro__media-inner" />
        </div>
      </div>
    </section>
  );
}
