import { Box, Network, Layers, Radio, Eye, FileCode } from "lucide-react"
import { Card } from "@/components/ui/card"

const features = [
  {
    icon: Box,
    title: "Modular 3D Assembly",
    description: "Compose reusable soil, topography, basin, foundation, pile, structure, and bridge-ready model parts into one assembled OpenSees system.",
  },
  {
    icon: Network,
    title: "Research-grade Partitioning",
    description: "Keep explicit control over domain decomposition so researchers can decide which regions, interfaces, or subsystems run on which cores.",
  },
  {
    icon: Layers,
    title: "Interfaces & Embedding",
    description: "Model embedded piles, embedded beams, embedded nodes, and other coupling strategies needed for demanding soil-structure interaction workflows.",
  },
  {
    icon: Radio,
    title: "Wave-input Workflows",
    description: "Generate DRM loads, consume H5DRM inputs, and compute transfer functions for site-response and wave-propagation studies when the workflow demands it.",
  },
  {
    icon: Eye,
    title: "In-Code Visualization",
    description: "Inspect mesh parts, assembly sections, and final assembled meshes directly from scripts or notebooks while you build and debug the model.",
  },
  {
    icon: FileCode,
    title: "Targeted Recording & Export",
    description: "Attach recorders and postprocessing logic to the regions that matter, then export to OpenSees workflows with the control needed for large studies.",
  },
]

export function Features() {
  return (
    <section id="features" className="py-20 px-4">
      <div className="container mx-auto">
        <div className="text-center mb-16 space-y-4">
          <h2 className="text-4xl md:text-5xl font-bold text-balance">
            {"Build Complex Models from"}
            <span className="block text-primary">Independent Expert Modules</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto text-pretty">
            {"Femora is designed so geotechnical, structural, and simulation experts can implement their own pieces independently and still assemble one coherent 3D OpenSees model."}
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <Card key={index} className="glass-strong p-6 hover:bg-card/50 transition-colors group">
              <div className="space-y-4">
                <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                  <feature.icon className="w-6 h-6 text-primary" />
                </div>
                <div className="space-y-2">
                  <h3 className="text-xl font-semibold">{feature.title}</h3>
                  <p className="text-muted-foreground leading-relaxed">{feature.description}</p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </section>
  )
}
