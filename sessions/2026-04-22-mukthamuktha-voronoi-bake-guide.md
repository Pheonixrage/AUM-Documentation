---
date: 2026-04-22
status: PROPOSED — needs user execution in Unity Editor
related: [[2026-04-22-pooling-plan]]
priority: HIGH (deal-breaker FPS issue on MukthaMuktha slash)
---

# MukthaMuktha Slash — Voronoi Bake-to-Texture Guide

## Why this matters

[`Axe_Slash.shadergraph`](../../AUM-Unity-Staging-Legacy/Assets/PFX Shaders/Axe_Slash.shadergraph) and [`Axe_Slash360.shadergraph`](../../AUM-Unity-Staging-Legacy/Assets/PFX Shaders/Axe_Slash360.shadergraph) contain:

- **8 VoronoiNode** instances (~40-60 ALU ops each)
- **7 PowerNode** instances (`pow(x, y)` is expensive on mobile)
- **2 GradientNoiseNode** instances
- Plus chained Multiply / Sin / Cos nodes feeding into them

Per-pixel cost: **~320-480 ALU ops on Mali-G37**. With 30-particle bursts × 2-3 mesh particle systems × full-screen weapon trail coverage, this dominates the slash frame budget across every platform.

The **Phase 1.2 commit** addresses this on mobile via VFXQueue scaling/disabling. **But to fully eliminate the cost without losing visuals on desktop**, we bake the Voronoi pattern to a texture and sample it instead of computing it every pixel.

**Expected gain:** 70-80% reduction in fragment shader cost. Visuals indistinguishable to players (shader Voronoi animation is fast enough that flipbook artifacts are masked by motion blur).

---

## Approach: Static Bake + UV Scroll (recommended — simplest)

The Voronoi pattern in Axe_Slash uses Time as input → animates. We have two bake strategies:

### Option A — Static Voronoi + UV Scroll (✅ RECOMMENDED)
- Bake one frame of Voronoi as a tileable 1024×1024 texture
- Replace 8 Voronoi nodes with one Sample Texture 2D node
- Scroll UVs over Time to fake the animation
- Visual: 95% identical to current (slash motion masks any pattern variance)
- Effort: ~1 hour
- VRAM: 1MB per shader (1024² RGBA8 with mipmaps)

### Option B — Flipbook (8 frames)
- Bake 8 time slices of Voronoi at 0.0, 0.125, 0.25... seconds into a 4×2 atlas
- Sample with frame-index based on particle lifetime
- Visual: 99% identical
- Effort: ~3 hours
- VRAM: 4MB per shader

**Go with Option A unless visual reviewer flags a difference.** The motion of a sword/axe slash is fast enough that no one will see the static pattern.

---

## Step-by-step (Option A — UV Scroll)

### Step 1: Bake the Voronoi texture

1. **Create a temporary scene** — `Assets/Scenes/_VoronoiBake.unity` (won't ship)
2. Add a **Quad** GameObject at world origin facing the camera
3. **Duplicate** `Brahma_Slash.mat` → name it `_VoronoiBake_Source.mat` (so you don't break the original)
4. Apply `_VoronoiBake_Source.mat` to the Quad
5. Position camera so the Quad fills exactly 1024×1024 of viewport
6. Set Camera **Background = solid black** (alpha 0)
7. Add this Editor script to capture (one-shot, throwaway):

```csharp
// Assets/Editor/VoronoiBaker.cs
using UnityEditor;
using UnityEngine;
using System.IO;

public static class VoronoiBaker
{
    [MenuItem("AUM/Bake Voronoi Slash Texture")]
    public static void BakeSelectedMaterial()
    {
        const int RES = 1024;
        var rt = new RenderTexture(RES, RES, 0, RenderTextureFormat.ARGB32);
        rt.useMipMap = false;

        // Render the active Camera (with Quad visible) to RT
        var cam = Camera.main;
        cam.targetTexture = rt;
        cam.Render();
        cam.targetTexture = null;

        // Read RT into Texture2D
        RenderTexture.active = rt;
        var tex = new Texture2D(RES, RES, TextureFormat.RGBA32, false);
        tex.ReadPixels(new Rect(0, 0, RES, RES), 0, 0);
        tex.Apply();
        RenderTexture.active = null;

        // Save PNG
        var path = "Assets/PFX Shaders/Axe_Slash_VoronoiBaked.png";
        File.WriteAllBytes(path, tex.EncodeToPNG());
        AssetDatabase.ImportAsset(path);

        // Set import settings (mipmaps on, sRGB off — it's pattern data, not color)
        var importer = AssetImporter.GetAtPath(path) as TextureImporter;
        if (importer != null)
        {
            importer.sRGBTexture = false;
            importer.mipmapEnabled = true;
            importer.wrapMode = TextureWrapMode.Repeat;
            importer.filterMode = FilterMode.Bilinear;
            importer.SaveAndReimport();
        }

        Object.DestroyImmediate(rt);
        Debug.Log($"[VoronoiBaker] Wrote {path}");
    }
}
```

8. Open `_VoronoiBake.unity`, position view, then run **AUM → Bake Voronoi Slash Texture**
9. Verify `Assets/PFX Shaders/Axe_Slash_VoronoiBaked.png` exists and looks like a Voronoi cell pattern
10. **Delete the temp scene + the bake script + `_VoronoiBake_Source.mat`** — you don't need them after

### Step 2: Modify the shader

1. Open `Assets/PFX Shaders/Axe_Slash.shadergraph`
2. **Don't delete the Voronoi nodes yet** — just bypass them
3. Add a **Sample Texture 2D** node, set Texture = `Axe_Slash_VoronoiBaked.png`
4. Add a **Tiling And Offset** node:
   - Tiling: (1, 1)
   - Offset: connect a **Time → Multiply by (0.5, 0.3)** for slow scroll
5. Connect Tiling And Offset's UV → Sample Texture 2D's UV
6. Find where the Voronoi outputs feed into Multiply / Color → **rewire** to use Sample Texture's R or G channel instead
7. **Save shader** — Unity recompiles
8. Visually verify in scene view that the slash still looks correct
9. Once happy, **delete the 8 Voronoi nodes** from the graph (and any Power nodes that fed only into them)
10. Repeat for `Axe_Slash360.shadergraph`

### Step 3: Verify perf

1. Build APK to a phone (or run in Editor with Profiler open, GPU profiler enabled)
2. Slash repeatedly as MukthaMuktha
3. Compare frame time before/after — should see **1-3ms saved per frame during slash on mobile**, ~0.5-1ms on Mac editor

---

## Approach: Pure Material Tier System (alternative — no shader changes)

If shader work is too much risk:

1. Duplicate Axe_Slash shadergraph → `Axe_Slash_Mobile.shadergraph`
2. In the duplicate, delete all 8 Voronoi nodes — replace output with constant color or solid texture
3. In `VFXQueue.cs`, instead of disabling/scaling, swap the material's shader at runtime based on platform

This gives you mobile = cheap shader, desktop = full shader. **No bake required**, but you lose the Voronoi look entirely on mobile.

---

## What NOT to do

- ❌ Don't reduce the burst count from 30 → fewer particles. The agent suggested this but it's a visual change you said you want to avoid.
- ❌ Don't use Unity's auto-LOD on shaders — it doesn't apply to ShaderGraph and won't selectively strip Voronoi.
- ❌ Don't try to convert ShaderGraph node-by-node to HLSL by hand — too error-prone.

---

## Status / sequence

1. ✅ **Phase 1.2 (committed):** VFXQueue.OptimizeExpensiveRenderers exposed publicly + PlayParticle hooked + GPU instancing enabled on 4 Axe_Slash materials
2. **Next:** Test Phase 1.2 on a phone — measure FPS during MukthaMuktha slash. If FPS is acceptable, ship as-is.
3. **If still bad:** Do Step 1-3 of "Static Bake + UV Scroll" above. ~1 hour of Editor work.
4. **Long term:** consider Option B (flipbook) if Option A's static pattern is visible in playtests.

---

*Generated: 2026-04-22 — research done in Phase 1.2 session of object pooling rollout*
