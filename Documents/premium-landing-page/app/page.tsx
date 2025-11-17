import { Navbar } from '@/components/Navbar';
import { Hero } from '@/components/Hero';
import { ProofSection } from '@/components/ProofSection';
import { Features } from '@/components/Features';
import { AttractorMode } from '@/components/AttractorMode';
import { ProductShowcase } from '@/components/ProductShowcase';
import { BeforeAfter } from '@/components/BeforeAfter';
import { Pricing } from '@/components/Pricing';
import { FAQ } from '@/components/FAQ';
import { EmailCapture } from '@/components/EmailCapture';
import { FinalCTA } from '@/components/FinalCTA';
import { ScrollProgress } from '@/components/ScrollProgress';

export default function Home() {
  return (
    <div className="bg-[#0a0a0f]">
      <ScrollProgress />
      <Navbar />
      <Hero />
      <ProofSection />
      <Features />
      <AttractorMode />
      <ProductShowcase />
      <BeforeAfter />
      <Pricing />
      <FAQ />
      <EmailCapture />
      <FinalCTA />
    </div>
  );
}
