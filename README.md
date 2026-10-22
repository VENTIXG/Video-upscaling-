# Video upscaling

## On your phone (AI upscale, free GPU)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/VENTIXG/Video-upscaling-/blob/master/upscale_colab.ipynb)

Upload your video to Google Drive, open the link above, and follow the steps in the notebook. The upscaled video is saved back to your Drive.

## On a computer

```bash
python upscale.py video.mp4              # 2x, ffmpeg (fast, CPU)
python upscale.py video.mp4 -m ai -s 4   # 4x with Real-ESRGAN (needs realesrgan-ncnn-vulkan)
```
