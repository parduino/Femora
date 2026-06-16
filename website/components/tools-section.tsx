import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ArrowRight, Box } from "lucide-react"
import { tools } from "@/lib/tools"

export function ToolsSection() {
  return (
    <section className="px-4 py-20">
      <div className="container mx-auto">
        <div className="mx-auto mb-14 max-w-3xl space-y-4 text-center">
          <h2 className="text-4xl font-bold text-balance md:text-5xl">
            {"Interactive"}
            <span className="block text-primary">Tools</span>
          </h2>
          <p className="text-xl text-muted-foreground text-pretty">
            {
              "These are browser-side utilities. They are separate from the documentation and API reference so you can open a focused helper immediately."
            }
          </p>
        </div>

        <div className="mx-auto grid max-w-6xl gap-6 lg:grid-cols-2">
          {tools.map((tool) => (
            <Card key={tool.title} className="glass-strong group flex h-full flex-col overflow-hidden p-0 transition-colors hover:bg-card/50">
              <div className="flex h-full flex-col">
                <div className="relative border-b border-border/60 bg-card/70">
                  {tool.previewUrl ? (
                    <div className="pointer-events-none relative h-64 overflow-hidden bg-card">
                      <div className="absolute inset-0 z-10 bg-gradient-to-b from-transparent via-transparent to-card/85" />
                      <iframe
                        src={tool.previewUrl}
                        title={`${tool.title} preview`}
                        className="absolute -left-0 -top-0 h-[1100px] w-[1700px] origin-top-left scale-[0.33] border-0"
                        tabIndex={-1}
                        aria-hidden="false"
                      />
                    </div>
                  ) : (
                    <div className="flex h-64 items-center justify-center bg-gradient-to-br from-primary/10 via-card/50 to-accent/10">
                      <div className="flex flex-col items-center gap-3 text-center">
                        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/12">
                          <Box className="h-8 w-8 text-primary" />
                        </div>
                        <div className="space-y-1">
                          <div className="text-sm font-semibold text-foreground">Preview Coming Later</div>
                          <div className="text-xs text-muted-foreground">The route is reserved. The tool is not built yet.</div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                <div className="space-y-3 px-7 pb-7 pt-6">
                  <h3 className="text-2xl font-semibold">{tool.title}</h3>
                  <p className="leading-relaxed text-muted-foreground">{tool.description}</p>

                  <div className="mt-auto pt-3">
                    <Button variant="outline" className="group/btn w-full bg-transparent" asChild>
                      <a href={tool.link}>
                        Open Tool
                        <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover/btn:translate-x-1" />
                      </a>
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </section>
  )
}
