import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Github } from "lucide-react"
import { ThemeToggle } from "@/components/theme-toggle"

export function Navigation() {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 glass border-b border-border/50">
      <div className="container mx-auto px-4 py-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <img src="/femora-logo.svg" alt="Femora logo" className="h-16 w-auto" />
            <span className="block font-bold text-lg sm:text-xl">Femora</span>
          </div>

          <div className="hidden md:flex items-center gap-8">
            <Link href="/#features" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Features
            </Link>
            <Link href="/#modes" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Workflows
            </Link>
            <Link href="/tools" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Tools
            </Link>
            <Link href="/#docs" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Documentation
            </Link>
            <Link href="/#ai" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              AI Direction
            </Link>
          </div>

          <div className="flex items-center gap-3">
            <ThemeToggle />
            <Button variant="ghost" size="sm" asChild>
              <a href="https://github.com/GeotechUW/Femora.git" target="_blank" rel="noopener noreferrer">
                <Github className="w-4 h-4" />
              </a>
            </Button>
            <Button size="sm" asChild>
              <a
                href="/docs/getting_started/"
              >
                Get Started
              </a>
            </Button>
          </div>
        </div>
      </div>
    </nav>
  )
}
