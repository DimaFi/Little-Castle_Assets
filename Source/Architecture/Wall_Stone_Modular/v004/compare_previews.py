"""Read-only image measurements against v003; generates JSON, never edits images."""
from pathlib import Path
import bpy, numpy as np, json
HERE=Path(__file__).resolve().parent
results=[]
for path in sorted((HERE/'Preview').glob('*.png')):
    old=HERE.parent/'v003/Preview'/path.name
    a=bpy.data.images.load(str(old),check_existing=False)
    b=bpy.data.images.load(str(path),check_existing=False)
    assert tuple(a.size)==tuple(b.size)
    x=np.empty(len(a.pixels),dtype=np.float32);y=np.empty_like(x)
    a.pixels.foreach_get(x);b.pixels.foreach_get(y)
    error=np.abs(x.reshape(-1,4)[:,:3]-y.reshape(-1,4)[:,:3])
    results.append({'image':path.name,'mean_abs_linear_rgb_error':float(error.mean()),
                    'max_abs_linear_rgb_error':float(error.max()),
                    'fraction_pixels_any_channel_error_above_0_01':float((error.max(axis=1)>.01).mean())})
    bpy.data.images.remove(a);bpy.data.images.remove(b)
report={'baseline':'v003','candidate':'v004','same_generator_camera_light_samples':True,
        'note':'Small indirect-light/denoising differences can occur after internal-face removal. Metrics are not an FPS test or a substitute for visual inspection.',
        'images':results}
(HERE/'QA/preview_comparison.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
