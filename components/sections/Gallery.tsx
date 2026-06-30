"use client";

import { useRef } from "react";
import { gsap, useGSAP } from "@/lib/gsap";

const CARDS = [
  { t: "Cadence", d: "Easing as rhythm" },
  { t: "Depth", d: "Layered parallax" },
  { t: "Focus", d: "Pinned narrative" },
  { t: "Restraint", d: "Less, but better" },
  { t: "Precision", d: "Composited only" },
  { t: "Flow", d: "Shared ticker" },
];

export default function Gallery() {
  const root = useRef<HTMLElement>(null);

  useGSAP(
    () => {
      const mm = gsap.matchMedia();

      // Horizontal scroll only where there's room and motion is welcome.
      mm.add(
        "(prefers-reduced-motion: no-preference) and (min-width: 760px)",
        () => {
          const track = root.current!.querySelector<HTMLElement>(".gallery__track")!;
          const distance = () => track.scrollWidth - window.innerWidth;

          gsap.to(track, {
            x: () => -distance(),
            ease: "none",
            scrollTrigger: {
              trigger: root.current,
              start: "top top",
              end: () => "+=" + distance(),
              scrub: true,
              pin: true,
              anticipatePin: 1,
              invalidateOnRefresh: true,
            },
          });
        }
      );
    },
    { scope: root }
  );

  return (
    <section ref={root} className="gallery" aria-label="Gallery">
      <div className="container" style={{ paddingBlock: "4rem 2rem" }}>
        <p className="eyebrow">Horizontal</p>
        <h2 className="display" style={{ fontSize: "clamp(1.8rem,4vw,3rem)", marginTop: "0.75rem" }}>
          A gallery that scrolls sideways.
        </h2>
      </div>
      <div className="gallery__track">
        {CARDS.map((c, i) => (
          <article className="gallery__card" key={c.t}>
            <span className="feature__num">{String(i + 1).padStart(2, "0")}</span>
            <div>
              <h3>{c.t}</h3>
              <p>{c.d}</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
