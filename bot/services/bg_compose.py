import io

from PIL import Image


def compose(subject: Image.Image, background: Image.Image, max_size: int = 2000) -> Image.Image:
    """Fonni to'liq holicha (kesmasdan) ishlatadi, faqat juda katta bo'lsa nisbatini
    saqlagan holda kichraytiradi. Sub'ekt fon ichiga (o'zi ham kesilmasdan) sig'diriladi va markazlashtiriladi."""
    subject = subject.convert("RGBA")
    bg = background.convert("RGBA")

    bg_w, bg_h = bg.size
    scale_down = min(1.0, max_size / max(bg_w, bg_h))
    if scale_down < 1.0:
        bg = bg.resize((max(1, round(bg_w * scale_down)), max(1, round(bg_h * scale_down))), Image.LANCZOS)
    canvas_w, canvas_h = bg.size

    subj_w, subj_h = subject.size
    fit_scale = min(canvas_w / subj_w, canvas_h / subj_h, 1.0)
    if fit_scale < 1.0:
        subject = subject.resize((max(1, round(subj_w * fit_scale)), max(1, round(subj_h * fit_scale))), Image.LANCZOS)

    result = bg.copy()
    x = (canvas_w - subject.width) // 2
    y = (canvas_h - subject.height) // 2
    result.paste(subject, (x, y), subject)
    return result.convert("RGB")


def flatten_on_white(image: Image.Image) -> Image.Image:
    """Shaffof (RGBA) rasmni oq fon ustiga tekislaydi, natija JPEG kabi shaffofliksiz formatlarga mos RGB bo'ladi."""
    rgba = image.convert("RGBA")
    white_bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    white_bg.paste(rgba, (0, 0), rgba)
    return white_bg.convert("RGB")


def image_to_bytes(image: Image.Image, fmt: str = "PNG", **save_kwargs) -> bytes:
    buf = io.BytesIO()
    image.save(buf, format=fmt, **save_kwargs)
    return buf.getvalue()
