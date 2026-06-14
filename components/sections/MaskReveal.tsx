"use client";

import { useRef } from "react";
import { gsap, useGSAP } from "@/lib/gsap";
import { textReveal } from "@/lib/animations";

export default function MaskReveal() {
  const root = useRef<HTMLElement>(null);

  useGSAP(
    () => {
      const mm = gsap.matchMedia();
      mm.add("(prefers-reduced-motion: no-preference)", () => {
        const heading = root.current!.querySelector<HTMLElement>(".mask__h");
        textReveal(heading!, "word");

        // Clip mask wipes open while the inner image settles from a scale-up.
        const tl = gsap.timeline({
          scrollTrigger: { trigger: ".mask__frame", start: "top 75%", once: true },
        });
        tl.to(".mask__frame", {
          clipPath: "inset(0% 0% 0% 0% round 16px)",
          duration: 1.1,
          ease: "power3.inOut",
        }).to(".mask__img", { scale: 1, duration: 1.4, ease: "power3.out" }, "<");

        // Slow continuous parallax drift while in view.
        gsap.to(".mask__img", {
          yPercent: -8,
          ease: "none",
          scrollTrigger: { trigger: ".mask__frame", start: "top bottom", end: "bottom top", scrub: true },
        });
      });
    },
    { scope: root }
  );

  return (
    <section ref={root} className="section container mask" aria-labelledby="mask-h">
      <p className="eyebrow" style={{ display: "inline-block" }}>
        Image reveal
      </p>
      <h2 id="mask-h" className="mask__h display" style={{ fontSize: "clamp(2rem,5vw,3.8rem)", marginTop: "1rem" }}>
        Reveals with a clean edge.
      </h2>
      <div className="mask__frame" aria-hidden>
        <div className="mask__img" />
      </div>
    </section>
  );
}
