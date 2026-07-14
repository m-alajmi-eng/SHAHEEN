# YOLOv8n Weights (download once, use offline)

The perception node loads a **pretrained YOLOv8n** model from this folder as
`best.pt`. Roboflow Universe is used **only as the one-time source** of the
weights. After download, the project runs fully offline — the node never
contacts any online service.

The weights file itself is **not committed** (see `.gitignore`); download it
once into this folder before building.

## Step 1 — Download the weights once

Pick the model whose classes match the runway hazards in the SHAHEEN world
(the traffic cone / FOD is the primary target). Suggested Roboflow Universe
models:

- Airport FOD: https://universe.roboflow.com/foreignobjectaerodromes/fod-i2kfx
- Traffic cone (fallback): https://universe.roboflow.com/cones-wte0i/cone-detection-t0r0x

Export the model in **YOLOv8** format and save the resulting weights here as:

```
ros2_ws/src/shaheen/models/best.pt
```

You can download either from the model's "Download Dataset / Model" page, or
once via the Roboflow Python package (run a single time, then delete the token):

```python
# one-time fetch — requires a free Roboflow API key
from roboflow import Roboflow
rf = Roboflow(api_key="YOUR_KEY")
project = rf.workspace("<workspace>").project("<project>")
model = project.version(<n>).model          # downloads the trained weights
# then copy the exported best.pt into this models/ folder
```

## Step 2 — Build so the weights are installed

```bash
cd ros2_ws
colcon build --packages-select shaheen_interfaces shaheen
source install/setup.bash
```

`setup.py` installs `models/*.pt` into the package share directory, and the
launch file points `model_path` at the installed `best.pt`.

## Notes

- Use the **nano** model (`yolov8n`) — it runs on CPU for SITL and needs no GPU.
- If the airport-FOD model does not fire reliably on the simulated cone, switch
  to the traffic-cone model — only the weights file changes; no code changes.
