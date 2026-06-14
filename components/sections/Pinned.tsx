"use client";

import { useRef } from "react";
import { gsap, useGSAP } from "@/lib/gsap";

const STEPS = [
  { k: "01", t: "Capture intent", d: "Motion begins with meaning — what should the eye do here?" },
  { k: "02", t: "Build the timeline", d: "One sequence, scrubbed to scroll. No scattered tweens." },
  { k: "03", t: "Tune to 60fps", d: "Transform and opacity only. Composited, never reflowed." },
];

export default function Pinned() {
  const root = useRef<HTMLElement>(null);

  useGSAP(
    () => {
      const mm = gsap.matchMedia();

      mm.add("(prefers-reduced-motion: no-preference)", () => {
        const steps = gsap.utils.toArray<HTMLElement>(".pin__step");

        // Pin the stage and scrub a master timeline that cross-fades steps.
        const tl = gsap.timeline({
          scrollTrigger: {
            trigger: root.current,
            start: "top top",
            end: () => "+=" + window.innerHeight * STEPS.length,
            scrub: true,
            pin: ".pin__stage",
            anticipatePin: 1,
          },
        });

        steps.forEach((step, i) => {
          if (i === 0) gsap.set(step, { autoAlpha: 1, yPercent: 0 });
          else {
            gsap.set(step, { autoAlpha: 0, yPercent: 12 });
            tl.to(steps[i - 1], { autoAlpha: 0, yPercent: -12, duration: 0.5 }).to(
              step,
              { autoAlpha: 1, yPercent: 0, duration: 0.5 },
              "<"
            );
          }
        });

        // Progress bar tracks the same pinned scroll range.
        gsap.to(".pin__progress > i", {
          scaleX: 1,
          ease: "none",
          scrollTrigger: {
            trigger: root.current,
            start: "top top",
            end: () => "+=" + window.innerHeight * STEPS.length,
            scrub: true,
          },
        });
      });

      // Reduced motion: show all steps stacked, no pin.
      mm.add("(prefers-reduced-motion: reduce)", () => {
        gsap.set(".pin__step", { autoAlpha: 1, position: "relative", yPercent: 0 });
        gsap.set(".pin__steps", { gap: "3rem" });
      });
    },
    { scope: root }
  );

  return (
    <section ref={root} className="pin" aria-label="How we build motion">
      <div className="pin__stage">
        <div className="container">
          <div className="pin__steps">
            {STEPS.map((s) => (
              <div className="pin__step" key={s.k}>
                <p className="eyebrow">{s.k}</p>
                <h2 className="display" style={{ marginTop: "1rem" }}>
                  {s.t}
                </h2>
                <p className="lead" style={{ margin: "1.5rem auto 0" }}>
                  {s.d}
                </p>
              </div>
            ))}
          </div>
          <div className="pin__progress" aria-hidden>
            <i />
          </div>
        </div>
      </div>
    </section>
  );
}
