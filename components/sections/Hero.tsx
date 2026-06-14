"use client";

import { useRef } from "react";
import { gsap, useGSAP } from "@/lib/gsap";
import { splitText, EASE } from "@/lib/animations";

export default function Hero() {
  const root = useRef<HTMLElement>(null);

  useGSAP(
    () => {
      const mm = gsap.matchMedia();

      mm.add("(prefers-reduced-motion: no-preference)", () => {
        const title = root.current!.querySelector<HTMLElement>(".hero__title")!;
        const words = splitText(title, "word");
        // Reveal the title container; the split words stay clipped in their
        // masks until the entrance tween slides them up, so there's no flash.
        gsap.set(title, { autoAlpha: 1 });

        const tl = gsap.timeline({ defaults: { ease: EASE.expo } });
        tl.from(".hero__eyebrow", { autoAlpha: 0, y: 20, duration: 0.8 })
          .from(words, { yPercent: 120, duration: 1.1, stagger: 0.09 }, "-=0.4")
          .from(".hero__lead", { autoAlpha: 0, y: 24, duration: 0.9 }, "-=0.7")
          .from(".hero__cue", { autoAlpha: 0, duration: 0.8 }, "-=0.4");

        // Subtle depth on scroll: glow drifts, title lifts and fades. Uses an
        // explicit fromTo so the scrubbed start state is always defined.
        gsap.to(".hero__glow", {
          yPercent: 30,
          ease: "none",
          scrollTrigger: { trigger: root.current, start: "top top", end: "bottom top", scrub: true },
        });
        gsap.fromTo(
          ".hero__title",
          { y: 0, autoAlpha: 1 },
          {
            y: -60,
            autoAlpha: 0.15,
            ease: "none",
            scrollTrigger: { trigger: root.current, start: "top top", end: "bottom top", scrub: true },
          }
        );

        // Pointer-driven 3D tilt (desktop only). Animates rotateX/rotateY only,
        // so it never collides with the scroll scrub's y/opacity tween.
        if (window.matchMedia("(pointer: fine)").matches) {
          const onMove = (e: PointerEvent) => {
            const nx = (e.clientX / window.innerWidth - 0.5) * 2;
            const ny = (e.clientY / window.innerHeight - 0.5) * 2;
            gsap.to(title, {
              rotateY: nx * 6,
              rotateX: -ny * 4,
              duration: 0.6,
              ease: EASE.out,
              overwrite: "auto",
            });
          };
          window.addEventListener("pointermove", onMove);
          return () => window.removeEventListener("pointermove", onMove);
        }
      });
    },
    { scope: root }
  );

  return (
    <header ref={root} className="hero" id="top">
      <div className="hero__glow" aria-hidden />
      <div className="container hero__inner">
        <p className="hero__eyebrow eyebrow reveal-hidden">Atelier · Est. MMXXVI</p>
        <h1 className="hero__title display reveal-hidden">
          Motion that feels engineered, not decorated.
        </h1>
        <p className="hero__lead lead reveal-hidden">
          A reference build for premium scroll storytelling — GSAP timelines,
          ScrollTrigger, and Lenis smooth scrolling, tuned for 60&nbsp;fps and
          fully respectful of reduced-motion preferences.
        </p>
      </div>
      <div className="hero__cue reveal-hidden" aria-hidden>
        Scroll
        <span />
      </div>
    </header>
  );
}
