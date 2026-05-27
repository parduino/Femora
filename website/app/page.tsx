import { Hero } from "@/components/hero"
import { Features } from "@/components/features"
import { WorkflowSection } from "@/components/workflow-section"
import { UseCasesSection } from "@/components/use-cases-section"
import { ModesSection } from "@/components/modes-section"
import { Documentation } from "@/components/documentation"
import { AISection } from "@/components/ai-section"
import { Footer } from "@/components/footer"
import { Navigation } from "@/components/navigation"

export default function Home() {
  return (
    <main className="min-h-screen bg-background relative overflow-hidden">
      {/* Background mesh pattern */}
      <div className="fixed inset-0 -z-10 opacity-20">
        <div
          className="absolute inset-0"
          style={{
            backgroundImage: `
            linear-gradient(to right, rgba(169, 116, 97, 0.08) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(169, 116, 97, 0.08) 1px, transparent 1px)
          `,
            backgroundSize: "40px 40px",
          }}
        ></div>
      </div>

      {/* Animated gradient orbs */}
      <div className="fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute top-1/4 -left-40 w-72 h-72 bg-primary/12 rounded-full blur-[72px] animate-pulse"></div>
        <div
          className="absolute bottom-1/4 -right-40 w-72 h-72 bg-accent/12 rounded-full blur-[72px] animate-pulse"
          style={{ animationDelay: "1s" }}
        ></div>
      </div>

      <Navigation />
      <Hero />
      <Features />
      <WorkflowSection />
      <UseCasesSection />
      <ModesSection />
      <Documentation />
      <AISection />
      <Footer />
    </main>
  )
}
