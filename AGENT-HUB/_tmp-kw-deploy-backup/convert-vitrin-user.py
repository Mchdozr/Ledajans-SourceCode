from __future__ import annotations

from pathlib import Path

from PIL import Image

src = Path(
    r"C:\Users\kacma\.cursor\projects\c-Users-kacma-Desktop-Ledajans-SourceCode\assets"
    r"\c__Users_kacma_AppData_Roaming_Cursor_User_workspaceStorage_7dfb9ce5533c561a018b26f3b896825b_images_image-2d95305a-5541-4afe-a0f1-39a37a8befb4.jpg"
)
dst = Path(__file__).resolve().parent / "media" / "magaza-vitrin-led-cadde.webp"
im = Image.open(src).convert("RGB")
print("src", im.size)
im = im.resize((1280, 720), Image.Resampling.LANCZOS)
dst.parent.mkdir(parents=True, exist_ok=True)
im.save(dst, "WEBP", quality=82, method=6)
print(dst.name, dst.stat().st_size)
