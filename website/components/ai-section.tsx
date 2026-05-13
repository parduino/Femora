import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Sparkles, Brain, Zap, MessageSquare } from "lucide-react"

export function AISection() {
  return (
    <section id="ai" className="py-20 px-4 relative overflow-hidden">
      {/* Decorative background elements */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-primary/5 rounded-full blur-3xl"></div>

      <div className="container mx-auto relative">
        <div className="text-center mb-16 space-y-4">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass text-sm">
            <Sparkles className="w-4 h-4 text-primary" />
            <span className="text-primary font-medium">AI-Native Direction</span>
          </div>
          <h2 className="text-4xl md:text-5xl font-bold text-balance">
            {"Structured for"}
            <span className="block text-primary">Future AI Workflows</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto text-pretty">
            {"Femora's modular, scriptable workflow is designed so future AI assistants can reason about model parts, assembly steps, interfaces, and recorder strategies instead of only generating disconnected scripts."}
          </p>
        </div>

        <div className="max-w-5xl mx-auto">
          <div className="grid md:grid-cols-3 gap-6 mb-12">
            <Card className="glass-strong p-6 space-y-4 hover:bg-card/50 transition-colors">
              <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
                <Brain className="w-6 h-6 text-primary" />
              </div>
              <div className="space-y-2">
                <h3 className="text-lg font-semibold">Model Generation</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {"Translate high-level modeling intent into reusable Femora modules and code-first workflows."}
                </p>
              </div>
            </Card>

            <Card className="glass-strong p-6 space-y-4 hover:bg-card/50 transition-colors">
              <div className="w-12 h-12 rounded-lg bg-accent/10 flex items-center justify-center">
                <MessageSquare className="w-6 h-6 text-accent" />
              </div>
              <div className="space-y-2">
                <h3 className="text-lg font-semibold">Interactive Assistant</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {"Help users understand assembly choices, interfaces, recorders, and decomposition decisions as the model grows."}
                </p>
              </div>
            </Card>

            <Card className="glass-strong p-6 space-y-4 hover:bg-card/50 transition-colors">
              <div className="w-12 h-12 rounded-lg bg-chart-3/10 flex items-center justify-center">
                <Zap className="w-6 h-6 text-chart-3" />
              </div>
              <div className="space-y-2">
                <h3 className="text-lg font-semibold">Smart Optimization</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {"Suggest cleaner partitioning, reusable modules, and better recording or postprocessing strategies for large studies."}
                </p>
              </div>
            </Card>
          </div>

          <Card className="glass-strong p-8 md:p-12 space-y-6">
            <div className="space-y-4 max-w-2xl">
              <h3 className="text-2xl font-bold">Why This Matters</h3>
              <p className="text-muted-foreground leading-relaxed">
                {
                  '"As the library grows, the same modular structure that helps researchers build large 3D systems also gives AI a cleaner representation of the model, its parts, and the engineering intent behind them."'
                }
              </p>
            </div>

            <div className="glass p-6 rounded-lg space-y-4">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0">
                  <Sparkles className="w-4 h-4 text-primary" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium mb-1">AI Response</p>
                  <p className="text-sm text-muted-foreground font-mono leading-relaxed">
                    {
                      '"I found your soil module, structural module, embedded interface, and recorder setup. I can now help modify the assembly, inspect the mesh, or generate a new OpenSees-ready workflow."'
                    }
                  </p>
                </div>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-4 pt-4">
              <Button size="lg" disabled className="flex-1">
                <Sparkles className="w-4 h-4 mr-2" />
                Join Waitlist
              </Button>
              <Button size="lg" variant="outline" className="flex-1 bg-transparent" asChild>
                <a href="https://github.com/amnp95/Femora/discussions" target="_blank" rel="noopener noreferrer">
                  Share Your Ideas
                </a>
              </Button>
            </div>
          </Card>
        </div>
      </div>
    </section>
  )
}
