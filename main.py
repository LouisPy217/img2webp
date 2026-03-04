import os
from pathlib import Path

from PIL import Image

from cli import parse_args

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
BATCH_OUTPUT_DIR = "compression_result"


def compress_image(
    input_path: str,
    output_path: str | None = None,
    lossless: bool = True,
    quality: int = 90,
    verbose: bool = False,
):
    """
    Compress a single image and save it as a WebP file.

    The output file is always saved in WebP format with the ``_compressed``
    suffix appended to its stem. If *output_path* is ``None``, the compressed
    file is saved next to the source image. Compression is performed with
    ``method=6`` (maximum effort), which yields the smallest file size at the
    cost of slower encoding.

    :param input_path: Path to the source image. Relative paths are resolved
        to absolute. Accepted formats are those supported by Pillow (e.g. JPEG, PNG).
    :param output_path: Destination path for the output file. The stem receives
        a ``_compressed`` suffix and the extension is replaced with ``.webp``.
        When ``None``, the output is placed in the same directory as the source.
    :param lossless: Enable lossless WebP compression. When ``False``, lossy
        compression is used and the *quality* parameter takes effect.
        Defaults to ``True``.
    :param quality: Lossy compression quality (1–100). Higher values produce
        better quality at larger file sizes. Ignored when *lossless* is ``True``.
        Defaults to ``90``.
    :param verbose: Print size statistics (original size, compressed size,
        reduction percentage) to stdout. Defaults to ``False``.
    :return: A tuple of ``(original_size, compressed_size)`` in bytes.
    :rtype: tuple[int, int]
    :raises FileNotFoundError: If *input_path* does not exist.
    :raises OSError: If the output file cannot be written.
    """
    input_path = Path(input_path)

    if not input_path.is_absolute():
        input_path = input_path.absolute()

    if output_path is None:
        output_path = Path(input_path).with_stem(input_path.stem + "_compressed").with_suffix(".webp")
    else:
        output_path_obj = Path(output_path)
        output_path = Path(output_path).with_stem(output_path_obj.stem + "_compressed").with_suffix(".webp")

    with Image.open(input_path) as img:
        if lossless:
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGBA" if "transparency" in img.info else "RGB")
        else:
            if img.mode == "P":
                img = img.convert("RGBA" if "transparency" in img.info else "RGB")
            elif img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGB")

        save_kwargs = {
            "format": "WEBP",
            "lossless": lossless,
            "method": 6,
        }

        if not lossless:
            save_kwargs["quality"] = quality

        img.save(output_path, **save_kwargs)

    original_size = os.path.getsize(input_path)
    compressed_size = os.path.getsize(output_path)
    ratio = (1 - compressed_size / original_size) * 100

    print("=" * 50)
    print(f"Complete: {output_path} image has been successfully compressed and converted.")

    if verbose:
        print(f"Original size:   {original_size / 1024:.1f} KB")
        print(f"Compressed size: {compressed_size / 1024:.1f} KB")
        print(f"Size reduced by: {ratio:.1f}%")

    return original_size, compressed_size


def batch_compress(
    input_dir: str,
    lossless: bool = True,
    quality: int = 90,
    verbose: bool = False,
) -> None:
    """
    Compress all supported images in a directory and save them as WebP files.

    Scans *input_dir* for files with extensions ``.jpg``, ``.jpeg``, and
    ``.png`` (non-recursive). Compressed files are written to the
    ``compression_result/`` subdirectory inside *input_dir*, which is created
    automatically if it does not exist. Each file is processed via
    :func:`compress_image`; a failure on an individual file is caught and
    reported without stopping the batch.

    A summary is printed to stdout after all files are processed, including
    the number of successfully converted files, total original and compressed
    sizes, and overall size reduction percentage.

    :param input_dir: Path to the directory containing source images.
        Relative paths are resolved to absolute.
    :param lossless: Enable lossless WebP compression for all images.
        When ``False``, lossy compression is used with the given *quality*.
        Defaults to ``True``.
    :param quality: Lossy compression quality (1–100). Ignored when
        *lossless* is ``True``. Defaults to ``90``.
    :param verbose: Pass verbose output to :func:`compress_image` for each
        processed file. Defaults to ``False``.
    :return: None
    """
    input_dir = Path(input_dir)

    if not input_dir.is_absolute():
        input_dir = input_dir.absolute()

    if not input_dir.is_dir():
        print(f"[E] '{input_dir}' is not a directory. Use --all only with a directory path.")
        return

    images = [
        img_file for img_file in input_dir.iterdir()
        if img_file.is_file() and img_file.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    if not images:
        print(f"No images ({', '.join(SUPPORTED_EXTENSIONS)}) found in '{input_dir}'.")
        return

    output_dir = input_dir / BATCH_OUTPUT_DIR
    output_dir.mkdir(exist_ok=True)

    total = len(images)

    print(f"Batch mode: found {total} image(s) in '{input_dir}'.")
    print("=" * 50)

    total_original = 0
    total_compressed = 0
    failed = []

    for idx, image_path in enumerate(images, start=1):
        output_path = output_dir / (image_path.stem + "_compressed.webp")

        print(f"[{idx}/{total}] Processing: {image_path.name}")

        try:
            original_size, compressed_size = compress_image(
                input_path=str(image_path),
                output_path=str(output_dir / image_path.stem),
                lossless=lossless,
                quality=quality,
                verbose=verbose,
            )

            total_original += original_size
            total_compressed += compressed_size
            ratio = (1 - compressed_size / original_size) * 100

            print(f"Done: {output_path.name}  ({ratio:.1f}% smaller)")
        except Exception as e:
            print(f"Failed: {e}")
            failed.append(image_path.name)

        print("-" * 50)

    succeeded = total - len(failed)

    print("=" * 50)
    print(f"Batch complete: {succeeded}/{total} image(s) converted successfully.")
    print(f"See the result in the directory: {output_dir}")

    if total_original > 0:
        total_ratio = (1 - total_compressed / total_original) * 100

        print(f"Total original size:    {total_original / 1024:.1f} KB")
        print(f"Total compressed size:  {total_compressed / 1024:.1f} KB")
        print(f"Overall size reduction: {total_ratio:.1f}%")

    if failed:
        print(f"\nFailed files ({len(failed)}):")

        for name in failed:
            print(f"\t- {name}")


def main():
    args = parse_args()

    if args.batch_mode:
        if args.output_path:
            print("[W] --output_path is ignored in batch mode.")
        batch_compress(
            input_dir=args.input_path,
            lossless=args.lossless,
            quality=args.quality,
            verbose=args.verbose,
        )
    else:
        compress_image(
            input_path=args.input_path,
            output_path=args.output_path,
            lossless=args.lossless,
            quality=args.quality,
            verbose=args.verbose,
        )


if __name__ == "__main__":
    main()
