# SSI Viewer Source

Replace [scene.vtk](/abs/path/D:/Projects/Femora/website/ssi-source/scene.vtk) with the SSI mesh you want to show on the homepage, then regenerate the embedded viewer:

```powershell
conda activate femora_debug
python scripts\export_ssi_viewer.py
```

You can also export a different file without replacing `scene.vtk`:

```powershell
conda activate femora_debug
python scripts\export_ssi_viewer.py --vtk path\to\your_model.vtk --title "Custom SSI model"
```
