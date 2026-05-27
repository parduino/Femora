import type { ReactNode } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Terminal, Layout, ArrowRight } from "lucide-react"

function CodeWindow({ lines }: { lines: ReactNode[] }) {
  return (
    <div className="overflow-hidden rounded-[1.35rem] border border-black/70 bg-[#0f0f0f] shadow-[0_22px_60px_rgba(0,0,0,0.32)]">
      <div className="flex items-center justify-between border-b border-white/8 bg-[#171717] px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-[#ff5f57]" />
          <span className="h-2.5 w-2.5 rounded-full bg-[#febc2e]" />
          <span className="h-2.5 w-2.5 rounded-full bg-[#28c840]" />
        </div>
        <span className="rounded-full border border-white/10 bg-white/[0.03] px-2.5 py-1 text-[0.66rem] font-medium uppercase tracking-[0.18em] text-white/45">
          Python
        </span>
      </div>
      <pre className="overflow-x-auto bg-[#101010] px-4 py-4 text-xs leading-7 text-[#f6eee8] sm:px-5 sm:text-sm">
        <code className="font-mono">
          {lines.map((line, index) => (
            <div key={index}>{line}</div>
          ))}
        </code>
      </pre>
    </div>
  )
}

export function ModesSection() {
  return (
    <section id="modes" className="relative px-4 py-20">
      <div className="container mx-auto">
        <div className="mb-16 space-y-4 text-center">
          <h2 className="text-4xl font-bold text-balance md:text-5xl">
            {"Two Practical"}
            <span className="block text-primary">Workflows</span>
          </h2>
          <p className="mx-auto max-w-2xl text-xl text-muted-foreground text-pretty">
            {"Femora stays scriptable for supercomputing workflows while still letting you inspect the model as it is being assembled."}
          </p>
        </div>

        <div className="mx-auto grid max-w-5xl gap-8 lg:grid-cols-2">
          <Card className="glass-strong group space-y-6 p-8 transition-all hover:bg-card/50">
            <div className="space-y-4">
              <div className="flex h-16 w-16 items-center justify-center rounded-xl bg-primary/10 transition-colors group-hover:bg-primary/20">
                <Terminal className="h-8 w-8 text-primary" />
              </div>
              <div className="space-y-2">
                <h3 className="text-2xl font-bold">Headless Mode</h3>
                <p className="leading-relaxed text-muted-foreground">
                  {
                    "Pure Python model construction for reproducible studies, HPC execution, automated exports, and large scripted model-generation pipelines."
                  }
                </p>
              </div>
            </div>

            <div className="space-y-3 pt-4">
              <div className="flex items-start gap-3">
                <div className="mt-2 h-1.5 w-1.5 rounded-full bg-primary" />
                <p className="text-sm text-muted-foreground">{"Scriptable and reproducible workflows"}</p>
              </div>
              <div className="flex items-start gap-3">
                <div className="mt-2 h-1.5 w-1.5 rounded-full bg-primary" />
                <p className="text-sm text-muted-foreground">{"Batch generation, export, and supercomputing workflows"}</p>
              </div>
              <div className="flex items-start gap-3">
                <div className="mt-2 h-1.5 w-1.5 rounded-full bg-primary" />
                <p className="text-sm text-muted-foreground">{"Parametric studies, modular reuse, and AI-ready code generation"}</p>
              </div>
            </div>

            <div className="pt-4">
              <CodeWindow
                lines={[
                  <>
                    <span className="text-[#d8a48f]">import</span> <span className="text-[#f6eee8]">femora</span>{" "}
                    <span className="text-[#d8a48f]">as</span> <span className="text-[#8ab4ff]">fm</span>
                  </>,
                  <></>,
                  <>
                    <span className="text-[#f6eee8]">model</span> <span className="text-white/70">=</span>{" "}
                    <span className="text-[#8ab4ff]">fm</span>
                    <span className="text-white/70">.</span>
                    <span className="text-[#7ed6c2]">MeshMaker</span>
                    <span className="text-white/70">()</span>
                  </>,
                  <>
                    <span className="text-white/35"># build materials, mesh parts, patterns, and assembly</span>
                  </>,
                  <>
                    <span className="text-[#f6eee8]">model</span>
                    <span className="text-white/70">.</span>
                    <span className="text-[#8ab4ff]">assembler</span>
                    <span className="text-white/70">.</span>
                    <span className="text-[#7ed6c2]">Assemble</span>
                    <span className="text-white/70">()</span>
                  </>,
                ]}
              />
            </div>

            <Button variant="outline" className="group/btn w-full bg-transparent" asChild>
              <a href="https://femora.io/docs/introduction/quick_start/" target="_blank" rel="noopener noreferrer">
                Learn More
                <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover/btn:translate-x-1" />
              </a>
            </Button>
          </Card>

          <Card className="glass-strong group space-y-6 p-8 transition-all hover:bg-card/50">
            <div className="space-y-4">
              <div className="flex h-16 w-16 items-center justify-center rounded-xl bg-accent/10 transition-colors group-hover:bg-accent/20">
                <Layout className="h-8 w-8 text-accent" />
              </div>
              <div className="space-y-2">
                <h3 className="text-2xl font-bold">Interactive Inspection</h3>
                <p className="leading-relaxed text-muted-foreground">
                  {
                    "Inspect mesh parts, assembly sections, interfaces, and final assembled meshes directly from Python or notebook cells without switching to a separate modeling product."
                  }
                </p>
              </div>
            </div>

            <div className="space-y-3 pt-4">
              <div className="flex items-start gap-3">
                <div className="mt-2 h-1.5 w-1.5 rounded-full bg-accent" />
                <p className="text-sm text-muted-foreground">{"Plot individual mesh parts during model creation"}</p>
              </div>
              <div className="flex items-start gap-3">
                <div className="mt-2 h-1.5 w-1.5 rounded-full bg-accent" />
                <p className="text-sm text-muted-foreground">{"Inspect assembly sections, interfaces, and the final assembled mesh"}</p>
              </div>
              <div className="flex items-start gap-3">
                <div className="mt-2 h-1.5 w-1.5 rounded-full bg-accent" />
                <p className="text-sm text-muted-foreground">{"Use from Python scripts, screenshots, and Jupyter workflows"}</p>
              </div>
            </div>

            <div className="pt-4">
              <CodeWindow
                lines={[
                  <>
                    <span className="text-[#d8a48f]">import</span> <span className="text-[#f6eee8]">femora</span>{" "}
                    <span className="text-[#d8a48f]">as</span> <span className="text-[#8ab4ff]">fm</span>
                  </>,
                  <></>,
                  <>
                    <span className="text-[#f6eee8]">model</span> <span className="text-white/70">=</span>{" "}
                    <span className="text-[#8ab4ff]">fm</span>
                    <span className="text-white/70">.</span>
                    <span className="text-[#7ed6c2]">MeshMaker</span>
                    <span className="text-white/70">()</span>
                  </>,
                  <>
                    <span className="text-[#f6eee8]">mesh_part</span>
                    <span className="text-white/70">.</span>
                    <span className="text-[#7ed6c2]">plot</span>
                    <span className="text-white/70">()</span>
                  </>,
                  <>
                    <span className="text-[#f6eee8]">model</span>
                    <span className="text-white/70">.</span>
                    <span className="text-[#8ab4ff]">assembler</span>
                    <span className="text-white/70">.</span>
                    <span className="text-[#7ed6c2]">plot</span>
                    <span className="text-white/70">(</span>
                    <span className="text-[#f6eee8]">show_edges</span>
                    <span className="text-white/70">=</span>
                    <span className="text-[#d8a48f]">True</span>
                    <span className="text-white/70">)</span>
                  </>,
                ]}
              />
            </div>

            <Button variant="outline" className="group/btn w-full bg-transparent" asChild>
              <a href="https://femora.io/docs/introduction/quick_start/" target="_blank" rel="noopener noreferrer">
                Learn More
                <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover/btn:translate-x-1" />
              </a>
            </Button>
          </Card>
        </div>
      </div>
    </section>
  )
}
