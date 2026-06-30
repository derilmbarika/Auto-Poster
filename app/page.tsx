import "./sections.css";
import Hero from "@/components/sections/Hero";
import Intro from "@/components/sections/Intro";
import Pinned from "@/components/sections/Pinned";
import Features from "@/components/sections/Features";
import MaskReveal from "@/components/sections/MaskReveal";
import Gallery from "@/components/sections/Gallery";
import SvgPath from "@/components/sections/SvgPath";
import Footer from "@/components/sections/Footer";

export default function Home() {
  return (
    <>
      <Hero />
      <main id="main">
        <Intro />
        <Pinned />
        <Features />
        <MaskReveal />
        <Gallery />
        <SvgPath />
      </main>
      <Footer />
    </>
  );
}
