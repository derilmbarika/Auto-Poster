"use client";

import { useEffect } from "react";
import Lenis from "lenis";
import { gsap, ScrollTrigger, prefersReducedMotion } from "@/lib/gsap";

/**
 * Initializes Lenis smooth scrolling and drives it from GSAP's ticker so that
 * Lenis and ScrollTrigger share a single render loop (no double rAF, no jank).
 *
 * When the user prefers reduced motion we skip Lenis entirely and fall back to
 * native scrolling — ScrollTrigger still works, it just reads the native scroll
 * position. Heavy scrubbed animations gate themselves on the same flag.
 */
export default function SmoothScroll({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    if (prefersReducedMotion()) return;

    const lenis = new Lenis({
      duration: 1.1,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)), // expo-out
      smoothWheel: true,
    });

    // Keep ScrollTrigger in sync with Lenis' virtual scroll position.
    lenis.on("scroll", ScrollTrigger.update);

    // Drive Lenis from the GSAP ticker; ticker uses seconds, Lenis wants ms.
    const raf = (time: number) => lenis.raf(time * 1000);
    gsap.ticker.add(raf);
    gsap.ticker.lagSmoothing(0);

    return () => {
      gsap.ticker.remove(raf);
      lenis.destroy();
    };
  }, []);

  return <>{children}</>;
}
