from pathlib import Path
import fitz
from PIL import Image

PDF_PATH = Path('api_test_cotizacion.pdf')
OUT_PATH = Path('api_test_cotizacion_table_preview.png')

if not PDF_PATH.exists():
    print('PDF not found:', PDF_PATH)
    raise SystemExit(1)

# Open document
doc = fitz.open(str(PDF_PATH))
page = doc.load_page(0)
page_rect = page.rect  # in points (1/72 inch)

# Render at zoom factor
zoom = 2  # 144 dpi
mat = fitz.Matrix(zoom, zoom)
pix = page.get_pixmap(matrix=mat, alpha=False)
img = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)

# Approximate table area in PDF points (based on template):
# left margin = 40pt, usable width ~= 532pt
left_pt = 40
right_pt = left_pt + 532
# choose vertical band to include header + first row
# header area approx between y=640pt (top) and y=520pt (bottom) in PDF coordinate (origin=bottom-left)
top_pt = 640
bottom_pt = 520

# Convert to pixel coords (image origin is top-left):
page_h_pts = page_rect.height

def pt_to_px_x(x_pt):
    return int(x_pt * zoom)

def pt_to_px_y(y_pt):
    # y_pt measured from bottom; image y px = (page_h_pts - y_pt) * zoom
    return int((page_h_pts - y_pt) * zoom)

left_px = pt_to_px_x(left_pt)
right_px = pt_to_px_x(right_pt)
top_px = pt_to_px_y(top_pt)
bottom_px = pt_to_px_y(bottom_pt)

# Ensure within image bounds
left_px = max(0, left_px)
top_px = max(0, top_px)
right_px = min(img.width, right_px)
bottom_px = min(img.height, bottom_px)

if top_px >= bottom_px or left_px >= right_px:
    print('Computed crop box invalid:', (left_px, top_px, right_px, bottom_px))
    raise SystemExit(2)

crop = img.crop((left_px, top_px, right_px, bottom_px))
# Optionally resize for easier viewing (handle Pillow versions)
resample = getattr(Image, 'LANCZOS', None)
if resample is None:
    # Pillow >=9 uses Image.Resampling
    resample = getattr(getattr(Image, 'Resampling', Image), 'LANCZOS', None)
if resample is None:
    # fallback to a known resampling constant across Pillow versions
    resample = getattr(getattr(Image, 'Resampling', Image), 'BICUBIC', None) or getattr(Image, 'BICUBIC', getattr(Image, 'NEAREST', None))
crop = crop.resize((int((right_px-left_px)*1.2), int((bottom_px-top_px)*1.2)), resample)

crop.save(OUT_PATH)
print('Saved table preview to', OUT_PATH)
