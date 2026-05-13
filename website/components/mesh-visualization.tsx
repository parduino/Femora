"use client"

export function MeshVisualization() {
  return (
    <div className="relative">
      <div className="glass-strong overflow-hidden rounded-[2rem] border border-white/12 p-3 shadow-2xl">
        <div className="relative overflow-hidden rounded-[1.5rem] bg-[#09111d]">
          <iframe
            src="/ssi-viewer/index.html?v=single-ssi-viewer-1"
            title="Femora soil-structure interaction mesh viewer"
            className="h-[620px] w-full border-0"
          />

          <div className="pointer-events-none absolute inset-x-0 top-0 flex items-start justify-between p-5">
            <div className="rounded-full border border-white/12 bg-black/30 px-3 py-1.5 text-[11px] font-medium uppercase tracking-[0.24em] text-white/72 backdrop-blur-md">
              Soil-Structure Interaction
            </div>
            <div className="rounded-full border border-cyan-300/18 bg-slate-950/36 px-3 py-1.5 text-[11px] text-cyan-100/78 backdrop-blur-md">
              Drag to orbit / scroll to zoom
            </div>
          </div>

          <div className="pointer-events-none absolute inset-x-0 bottom-0 bg-gradient-to-t from-[#050b14] via-[#050b14]/84 to-transparent p-6">
            <div className="max-w-md space-y-2">
              <div className="text-xs font-medium uppercase tracking-[0.28em] text-cyan-200/68">
                Live mesh scene
              </div>
              <p className="text-sm leading-6 text-slate-200/78">
                This viewer is exported from the project VTK scene, so the website shows the actual
                SSI model instead of a synthetic hero animation.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="absolute -bottom-8 -right-6 h-36 w-36 rounded-full bg-cyan-400/10 blur-3xl" />
      <div className="absolute -left-6 -top-8 h-32 w-32 rounded-full bg-emerald-300/8 blur-3xl" />
    </div>
  )
}
