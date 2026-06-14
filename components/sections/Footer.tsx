"use client";

import { useRef } from "react";
import { gsap, useGSAP } from "@/lib/gsap";
import { textReveal } from "@/lib/animations";

export default function Footer() {
  const root = useRef<HTMLElement>(null);

  useGSAP(
    () => {
      const mm = gsap.matchMedia();
      mm.add("(prefers-reduced-motion: no-preference)", () => {
        const big = root.current!.querySelector<HTMLElement>(".footer__big");
        textReveal(big!, "char", { stagger: 0.025 });
      });
    },
    { scope: root }
  );

  return (
    <footer ref={root} className="footer" id="contact">
      <div className="container">
        <h2 className="footer__big">Let&rsquo;s move.</h2>
        <div className="footer__row">
          <span>Built with GSAP · ScrollTrigger · Lenis</span>
          <nav aria-label="Footer">
            <a href="#top">Back to top</a>
          </nav>
        </div>
      </div>
    </footer>
  );
}
