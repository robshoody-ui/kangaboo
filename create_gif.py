#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageFilter

PROJECT_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = PROJECT_DIR / "kangaroo_punch.gif"
NUMBER_BOX = (12, 10, 44, 44)
NUMBER_DONOR_OFFSET = (36, 0)


def ensure_pillow():
    try:
        import PIL  # noqa: F401
    except ImportError as exc:
        raise SystemExit(
            "Fehler: Pillow ist nicht installiert.\n"
            "Installiere es mit: python -m pip install pillow"
        ) from exc


def load_frames():
    expected_paths = [PROJECT_DIR / f"{index:02d}.png" for index in range(1, 13)]
    missing = [path.name for path in expected_paths if not path.exists()]
    if missing:
        raise SystemExit(
            "Fehler: Fehlende Bilddateien im Projektordner.\n"
            f"Fehlt: {', '.join(missing)}\n"
            "Erwarte: 01.png bis 12.png"
        )

    frames = []
    for path in expected_paths:
        try:
            frame = Image.open(path).convert("RGBA")
        except Exception as exc:
            raise SystemExit(f"Fehler: Bild konnte nicht geladen werden: {path.name} ({exc})") from exc
        frames.append(frame)
    return frames


def remove_corner_number(frame):
    left, top, right, bottom = NUMBER_BOX
    width = right - left
    height = bottom - top
    donor_x = left + NUMBER_DONOR_OFFSET[0]
    donor_y = top + NUMBER_DONOR_OFFSET[1]
    if donor_x + width > frame.width or donor_y + height > frame.height:
        raise SystemExit(
            f"Fehler: Das Bild {frame.size} ist zu klein für die einstellbare Nummernretusche."
        )

    donor = frame.crop((donor_x, donor_y, donor_x + width, donor_y + height))
    mask = Image.new("L", (width, height), 0)
    mask.paste(255, (4, 4, width - 4, height - 4))
    mask = mask.filter(ImageFilter.GaussianBlur(3))
    frame.paste(donor, (left, top), mask)
    return frame


def validate_frame_sizes(frames):
    sizes = {frame.size for frame in frames}
    if len(sizes) != 1:
        detail = ", ".join(f"{index + 1:02d}.png: {frame.size}" for index, frame in enumerate(frames))
        raise SystemExit(
            "Fehler: Nicht alle PNGs haben dieselbe Bildgröße. "
            "Die Bilder werden nicht skaliert oder beschnitten.\n"
            f"Gefundene Größen: {detail}"
        )
    return frames


def build_animation(frames):
    durations = [200, 200, 200, 140, 140, 140, 90, 90, 90, 200, 255, 255]
    if len(frames) != 12:
        raise SystemExit(f"Fehler: Erwartet 12 Bilder, gefunden: {len(frames)}")

    return frames, durations


def save_gif(frames, durations):
    width, height = frames[0].size
    palette_source = Image.new("RGB", (width, height * len(frames)))
    for index, frame in enumerate(frames):
        palette_source.paste(frame.convert("RGB"), (0, index * height))
    palette = palette_source.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    paletted_frames = [
        frame.convert("RGB").quantize(palette=palette, dither=Image.Dither.FLOYDSTEINBERG)
        for frame in frames
    ]
    paletted_frames[0].save(
        OUTPUT_PATH,
        save_all=True,
        append_images=paletted_frames[1:],
        duration=durations,
        loop=0,
        optimize=False,
        disposal=2,
    )


def main():
    ensure_pillow()
    frames = load_frames()
    validate_frame_sizes(frames)
    frames = [remove_corner_number(frame) for frame in frames]
    frames, durations = build_animation(frames)
    save_gif(frames, durations)
    print(f"GIF erfolgreich erstellt: {OUTPUT_PATH.resolve()}")
    print(f"Frames: {len(frames)} | Schleife: endlos")


if __name__ == "__main__":
    main()
