import { Card } from "@/components/ui/card"
import { Building2, Mountain, Radio, Waypoints } from "lucide-react"

const useCases = [
  {
    icon: Mountain,
    title: "Site Response and Basin Models",
    description:
      "Build layered soil domains, topography-aware regions, and basin-scale studies while preserving modular control over each part of the model.",
    stack: ["Soil modules", "Topography", "Recorder regions"],
  },
  {
    icon: Building2,
    title: "Soil-Structure Interaction",
    description:
      "Assemble soil, foundations, piles, structures, and coupling interfaces into one 3D workflow that can still be inspected and refined during development.",
    stack: ["Structures", "Foundations", "Embedded strategies"],
  },
  {
    icon: Radio,
    title: "Wave-input and DRM Workflows",
    description:
      "Generate DRM loads, consume wave-input data, and compute transfer-function oriented workflows when site-response or input-motion studies require them.",
    stack: ["DRM loads", "H5DRM input", "Transfer functions"],
  },
  {
    icon: Waypoints,
    title: "Bridge-ready and Multi-system Assemblies",
    description:
      "Compose multiple expert-owned subsystems into one partition-aware research model without flattening the workflow into an unmaintainable script.",
    stack: ["Sub-assemblies", "Core decomposition", "Targeted recorders"],
  },
]

export function UseCasesSection() {
  return (
    <section id="use-cases" className="px-4 py-20">
      <div className="container mx-auto">
        <div className="mb-16 space-y-4 text-center">
          <h2 className="text-4xl font-bold text-balance md:text-5xl">
            {"What You Can"}
            <span className="block text-primary">Build With It</span>
          </h2>
          <p className="mx-auto max-w-3xl text-xl text-muted-foreground text-pretty">
            {
              "Femora is most useful when the model is too large, too modular, or too collaborative to live comfortably in one handwritten OpenSees script."
            }
          </p>
        </div>

        <div className="mx-auto grid max-w-6xl gap-6 md:grid-cols-2">
          {useCases.map((useCase) => (
            <Card key={useCase.title} className="glass-strong group p-7 transition-colors hover:bg-card/50">
              <div className="space-y-5">
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 transition-colors group-hover:bg-primary/20">
                  <useCase.icon className="h-7 w-7 text-primary" />
                </div>

                <div className="space-y-3">
                  <h3 className="text-2xl font-semibold">{useCase.title}</h3>
                  <p className="leading-relaxed text-muted-foreground">{useCase.description}</p>
                </div>

                <div className="flex flex-wrap gap-2">
                  {useCase.stack.map((item) => (
                    <span
                      key={item}
                      className="rounded-full border border-border/70 bg-card/70 px-3 py-1 text-xs font-medium tracking-[0.04em] text-muted-foreground"
                    >
                      {item}
                    </span>
                  ))}
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </section>
  )
}
