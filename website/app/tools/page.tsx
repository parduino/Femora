import { Footer } from "@/components/footer"
import { Navigation } from "@/components/navigation"
import { ToolsSection } from "@/components/tools-section"

export default function ToolsPage() {
  return (
    <main className="relative min-h-screen overflow-hidden bg-background">
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

      <div className="fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute -left-40 top-1/4 h-72 w-72 rounded-full bg-primary/12 blur-[72px]"></div>
        <div className="absolute -right-40 bottom-1/4 h-72 w-72 rounded-full bg-accent/12 blur-[72px]"></div>
      </div>

      <Navigation />

      <section className="px-4 pb-10 pt-32">
        <div className="container mx-auto">
          <div className="mx-auto max-w-4xl space-y-6 text-center">
            <span className="inline-flex rounded-full border border-border/70 bg-card/70 px-4 py-2 text-xs font-medium uppercase tracking-[0.2em] text-muted-foreground">
              Femora utilities
            </span>
            <h1 className="text-5xl font-bold text-balance md:text-6xl">
              {"Open the tool,"}
              <span className="block text-primary">do the task, move on</span>
            </h1>
            <p className="mx-auto max-w-3xl text-xl leading-relaxed text-muted-foreground text-pretty">
              {
                "Use the documentation to learn Femora. Use this area when you want an interactive utility such as a damping explorer or a viewer without digging through scripts or generated files."
              }
            </p>
          </div>
        </div>
      </section>

      <ToolsSection />
      <Footer />
    </main>
  )
}
