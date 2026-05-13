import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Terminal, Layout, ArrowRight } from "lucide-react"

export function ModesSection() {
  return (
    <section id="modes" className="py-20 px-4 relative">
      <div className="container mx-auto">
        <div className="text-center mb-16 space-y-4">
          <h2 className="text-4xl md:text-5xl font-bold text-balance">
            {"Two Practical"}
            <span className="block text-primary">Workflows</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto text-pretty">
            {"Femora stays scriptable for supercomputing workflows while still letting you inspect the model as it is being assembled."}
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8 max-w-5xl mx-auto">
          {/* Headless Mode */}
          <Card className="glass-strong p-8 space-y-6 hover:bg-card/50 transition-all group">
            <div className="space-y-4">
              <div className="w-16 h-16 rounded-xl bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                <Terminal className="w-8 h-8 text-primary" />
              </div>
              <div className="space-y-2">
                <h3 className="text-2xl font-bold">Headless Mode</h3>
                <p className="text-muted-foreground leading-relaxed">
                  {
                    "Pure Python model construction for reproducible studies, HPC execution, automated exports, and large scripted model-generation pipelines."
                  }
                </p>
              </div>
            </div>

            <div className="space-y-3 pt-4">
              <div className="flex items-start gap-3">
                <div className="w-1.5 h-1.5 rounded-full bg-primary mt-2"></div>
                <p className="text-sm text-muted-foreground">{"Scriptable and reproducible workflows"}</p>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-1.5 h-1.5 rounded-full bg-primary mt-2"></div>
                <p className="text-sm text-muted-foreground">{"Batch generation, export, and supercomputing workflows"}</p>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-1.5 h-1.5 rounded-full bg-primary mt-2"></div>
                <p className="text-sm text-muted-foreground">{"Parametric studies, modular reuse, and AI-ready code generation"}</p>
              </div>
            </div>

            <div className="pt-4">
              <pre className="glass p-4 rounded-lg text-xs font-mono overflow-x-auto">
                <code className="text-accent">{`import femora as fm

model = fm.MeshMaker()
# build materials, mesh parts, patterns, and assembly
model.assembler.Assemble()`}</code>
              </pre>
            </div>

            <Button variant="outline" className="w-full group/btn bg-transparent" asChild>
              <a
                href="https://amnp95.github.io/Femora/introduction/quick_start.html"
                target="_blank"
                rel="noopener noreferrer"
              >
                Learn More
                <ArrowRight className="w-4 h-4 ml-2 group-hover/btn:translate-x-1 transition-transform" />
              </a>
            </Button>
          </Card>

          {/* In-Code Visualization */}
          <Card className="glass-strong p-8 space-y-6 hover:bg-card/50 transition-all group">
            <div className="space-y-4">
              <div className="w-16 h-16 rounded-xl bg-accent/10 flex items-center justify-center group-hover:bg-accent/20 transition-colors">
                <Layout className="w-8 h-8 text-accent" />
              </div>
              <div className="space-y-2">
                <h3 className="text-2xl font-bold">Interactive Inspection</h3>
                <p className="text-muted-foreground leading-relaxed">
                  {
                    "Inspect mesh parts, assembly sections, interfaces, and final assembled meshes directly from Python or notebook cells without switching to a separate modeling product."
                  }
                </p>
              </div>
            </div>

            <div className="space-y-3 pt-4">
              <div className="flex items-start gap-3">
                <div className="w-1.5 h-1.5 rounded-full bg-accent mt-2"></div>
                <p className="text-sm text-muted-foreground">{"Plot individual mesh parts during model creation"}</p>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-1.5 h-1.5 rounded-full bg-accent mt-2"></div>
                <p className="text-sm text-muted-foreground">{"Inspect assembly sections, interfaces, and the final assembled mesh"}</p>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-1.5 h-1.5 rounded-full bg-accent mt-2"></div>
                <p className="text-sm text-muted-foreground">{"Use from Python scripts, screenshots, and Jupyter workflows"}</p>
              </div>
            </div>

            <div className="pt-4">
              <pre className="glass p-4 rounded-lg text-xs font-mono overflow-x-auto">
                <code className="text-accent">{`import femora as fm

model = fm.MeshMaker()
mesh_part.plot()
model.assembler.plot(show_edges=True)`}</code>
              </pre>
            </div>

            <Button variant="outline" className="w-full group/btn bg-transparent" asChild>
              <a
                href="https://amnp95.github.io/Femora/introduction/quick_start.html"
                target="_blank"
                rel="noopener noreferrer"
              >
                Learn More
                <ArrowRight className="w-4 h-4 ml-2 group-hover/btn:translate-x-1 transition-transform" />
              </a>
            </Button>
          </Card>
        </div>
      </div>
    </section>
  )
}
