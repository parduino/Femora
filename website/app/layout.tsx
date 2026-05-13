import type React from "react"
import type { Metadata } from "next"

import { Analytics } from "@vercel/analytics/next"
import { ThemeProvider } from "@/components/theme-provider"
import "./globals.css"

import { Inter, JetBrains_Mono, Geist as V0_Font_Geist, Geist_Mono as V0_Font_Geist_Mono, Bree_Serif as V0_Font_Bree_Serif } from 'next/font/google'

// Initialize fonts
const _geist = V0_Font_Geist({ subsets: ['latin'], weight: ["100","200","300","400","500","600","700","800","900"] })
const _geistMono = V0_Font_Geist_Mono({ subsets: ['latin'], weight: ["100","200","300","400","500","600","700","800","900"] })
const _breeSerif = V0_Font_Bree_Serif({ subsets: ['latin'], weight: ["400"] })

const inter = Inter({ subsets: ["latin"] })
const jetbrainsMono = JetBrains_Mono({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "FEMORA - Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis",
  description: "An open-source Python platform for modular 3D meta-modeling, assembly, and OpenSees export for resilience analysis.",
  generator: "v0.app",
  icons: {
    icon: "docs/assets/femora-mark.svg",
    shortcut: "docs/assets/femora-mark.svg",
    apple: "docs/assets/femora-mark.svg",
  },
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`font-serif antialiased`}>
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem storageKey="femora-ui-theme">
          {children}
        </ThemeProvider>
        <Analytics />
      </body>
    </html>
  )
}
