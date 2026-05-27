import { Card } from "@/components/ui/card"
import { Blocks, Combine, Eye, Send } from "lucide-react"

const steps = [
  {
    icon: Blocks,
    title: "Build Independent Modules",
    description:
      "Create reusable soil, structure, interface, loading, and recorder components with the manager that owns each concern.",
  },
  {
    icon: Combine,
    title: "Assemble One 3D Model",
    description:
      "Combine independently authored pieces into one coherent OpenSees-ready assembly while keeping control over partition-aware workflows.",
  },
  {
    icon: Eye,
    title: "Inspect While Coding",
    description:
      "Plot mesh parts, interfaces, assembly sections, and final meshes directly from Python or notebook cells as the model evolves.",
  },
  {
    icon: Send,
    title: "Export and Study",
    description:
      "Attach targeted recorders, run wave-input workflows when needed, and push the assembled model into larger analysis studies.",
  },
]

export function WorkflowSection() {
  return (
    <section id="workflow" className="px-4 py-20">
      <div className="container mx-auto">
        <div className="mb-16 space-y-4 text-center">
          <h2 className="text-4xl font-bold text-balance md:text-5xl">
            {"How Femora"}
            <span className="block text-primary">Actually Works</span>
          </h2>
          <p className="mx-auto max-w-3xl text-xl text-muted-foreground text-pretty">
            {
              "Femora is not just a mesher and not just a script wrapper. It is an assembly workflow for turning independently developed engineering modules into one inspectable 3D OpenSees model."
            }
          </p>
        </div>

        <div className="mx-auto grid max-w-6xl gap-6 md:grid-cols-2 xl:grid-cols-4">
          {steps.map((step, index) => (
            <Card key={step.title} className="glass-strong group relative p-6 transition-colors hover:bg-card/50">
              <div className="mb-5 flex items-center justify-between">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 transition-colors group-hover:bg-primary/20">
                  <step.icon className="h-6 w-6 text-primary" />
                </div>
                <span className="text-sm font-semibold text-muted-foreground/70">{`0${index + 1}`}</span>
              </div>
              <div className="space-y-2">
                <h3 className="text-xl font-semibold">{step.title}</h3>
                <p className="leading-relaxed text-muted-foreground">{step.description}</p>
              </div>
            </Card>
          ))}
        </div>

        <div className="glass-strong mx-auto mt-10 max-w-6xl rounded-[2rem] p-8 md:p-10">
          <div className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
            <div className="space-y-5">
              <div className="inline-flex rounded-full border border-border/70 bg-card/60 px-3 py-1 text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
                Workflow Logic
              </div>
              <h3 className="text-2xl font-bold md:text-3xl">From expert-owned pieces to one coherent model</h3>
              <p className="max-w-2xl leading-relaxed text-muted-foreground">
                {
                  "Geotechnical, structural, and simulation specialists can implement different parts independently. Femora gives those parts a shared assembly language so you can inspect the process, keep decomposition explicit, and scale from a simple study to a larger research workflow."
                }
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
              <div className="rounded-2xl border border-border/70 bg-card/70 p-4">
                <div className="mb-2 text-sm font-semibold text-foreground">Inputs</div>
                <p className="text-sm leading-relaxed text-muted-foreground">
                  Soil modules, structures, interfaces, loading, recorders, and partitioning choices.
                </p>
              </div>
              <div className="rounded-2xl border border-border/70 bg-card/70 p-4">
                <div className="mb-2 text-sm font-semibold text-foreground">Assembly</div>
                <p className="text-sm leading-relaxed text-muted-foreground">
                  Assemble, inspect, refine, and coordinate mesh regions without collapsing everything into one script.
                </p>
              </div>
              <div className="rounded-2xl border border-border/70 bg-card/70 p-4">
                <div className="mb-2 text-sm font-semibold text-foreground">Output</div>
                <p className="text-sm leading-relaxed text-muted-foreground">
                  OpenSees-ready workflows, targeted recording logic, screenshots, and reproducible research pipelines.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
