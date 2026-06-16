import type { LucideIcon } from "lucide-react"
import { Box, SlidersHorizontal, Activity } from "lucide-react"

export type ToolStatus = "Available" | "Planned"

export type ToolDefinition = {
  slug: string
  title: string
  description: string
  link: string
  status: ToolStatus
  icon: LucideIcon
  previewUrl?: string
}

export const tools: ToolDefinition[] = [
  {
    slug: "rayleigh",
    title: "Rayleigh Damping Explorer",
    description:
      "Explore target frequencies, damping ratios, and explicit Rayleigh coefficients in the browser.",
    link: "/tools/rayleigh/",
    status: "Available",
    icon: SlidersHorizontal,
    previewUrl: "/tools/rayleigh/",
  },
  {
    slug: "transfer-function",
    title: "Transfer Function Explorer",
    description: "Compute 1D shear-wave transfer functions for layered soil columns fully in the browser.",
    link: "/tools/transfer-function/",
    status: "Available",
    icon: Activity,
    previewUrl: "/tools/transfer-function/",
  },
  {
    slug: "mesh-viewer",
    title: "Mesh Viewer",
    description:
      "Reserved for a future browser-based Femora mesh and partition viewer.",
    link: "/tools/",
    status: "Planned",
    icon: Box,
  },
]
