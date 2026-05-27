import { Github, FileText } from "lucide-react"

export function Footer() {
  return (
    <footer className="mt-20 border-t border-border/50 px-4 py-12">
      <div className="container mx-auto">
        <div className="mb-8 grid gap-8 md:grid-cols-4">
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <img src="/femora-logo.svg" alt="Femora logo" className="h-12 w-auto" />
              <span className="block text-xl font-bold">Femora</span>
            </div>
            <p className="text-sm leading-relaxed text-muted-foreground">
              {"Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis"}
            </p>
          </div>

          <div className="space-y-4">
            <h4 className="font-semibold">Documentation</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a href="/docs/getting_started/" className="text-muted-foreground transition-colors hover:text-foreground">
                  Getting Started
                </a>
              </li>
              <li>
                <a href="/docs/installation/" className="text-muted-foreground transition-colors hover:text-foreground">
                  Installation
                </a>
              </li>
              <li>
                <a href="/docs/advanced/" className="text-muted-foreground transition-colors hover:text-foreground">
                  Examples
                </a>
              </li>
              <li>
                <a href="/docs/reference/" className="text-muted-foreground transition-colors hover:text-foreground">
                  API Reference
                </a>
              </li>
            </ul>
          </div>

          <div className="space-y-4">
            <h4 className="font-semibold">Resources</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a
                  href="https://github.com/GeotechUW/Femora"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-muted-foreground transition-colors hover:text-foreground"
                >
                  GitHub Repository
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/GeotechUW/Femora/issues"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-muted-foreground transition-colors hover:text-foreground"
                >
                  Issue Tracker
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/GeotechUW/Femora/discussions"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-muted-foreground transition-colors hover:text-foreground"
                >
                  Discussions
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/GeotechUW/Femora"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-muted-foreground transition-colors hover:text-foreground"
                >
                  Contributing
                </a>
              </li>
            </ul>
          </div>

          <div className="space-y-4">
            <h4 className="font-semibold">Connect</h4>
            <div className="flex gap-3">
              <a
                href="https://github.com/GeotechUW/Femora"
                target="_blank"
                rel="noopener noreferrer"
                className="flex h-10 w-10 items-center justify-center rounded-lg bg-secondary transition-colors hover:bg-primary/20"
              >
                <Github className="h-5 w-5" />
              </a>
              <a href="/docs/" className="flex h-10 w-10 items-center justify-center rounded-lg bg-secondary transition-colors hover:bg-primary/20">
                <FileText className="h-5 w-5" />
              </a>
            </div>
          </div>
        </div>

        <div className="flex flex-col items-center justify-between gap-4 border-t border-border/50 pt-8 text-sm text-muted-foreground md:flex-row">
          <p>{"© 2025 Femora. Open-source platform developed by Amin Pakzad & Pedro Arduino"}</p>
          <div className="flex gap-6">
            <a
              href="https://github.com/GeotechUW/Femora/blob/main/LICENSE"
              target="_blank"
              rel="noopener noreferrer"
              className="transition-colors hover:text-foreground"
            >
              License
            </a>
            <a
              href="https://github.com/GeotechUW/Femora"
              target="_blank"
              rel="noopener noreferrer"
              className="transition-colors hover:text-foreground"
            >
              GitHub
            </a>
          </div>
        </div>
      </div>
    </footer>
  )
}
