import argparse


def parse_args():
    """
    Parse command-line arguments for the image-to-WebP converter.
    Builds an argument parser with the following arguments:

    :param input_path: Path to the input image or directory (positional).
    :type input_path: str
    :param output_path: Path to the output WebP file. Optional.
    :type output_path: str or None
    :param lossless: If set, convert using lossless compression.
    :type lossless: bool
    :param quality: Compression quality level (0–100). Defaults to 90.
    :type quality: int
    :param verbose: If set, print verbose output during conversion.
    :type verbose: bool
    :param batch_mode: If set, convert all .jpg/.jpeg/.png images in the
        input_path directory.
    :type batch_mode: bool

    :returns: Parsed argument namespace.
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(
        description="Converts and compresses images to WebP format.",
    )

    parser.add_argument(
        "input_path",
        type=str,
        help="Input: path to the image file to convert to WebP",
    )

    parser.add_argument(
        "--output_path",
        type=str,
        help="Output: path to save the resulting WebP file (default: same location as input)",
    )
    parser.add_argument(
        "--lossless",
        action="store_true",
        help="Lossless mode: use lossless compression instead of lossy",
    )
    parser.add_argument(
        "--quality",
        default=90,
        type=int,
        help="Quality: compression quality level from 0 (worst) to 100 (best), default is 90",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose mode: print detailed progress and conversion info",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="batch_mode",
        help="Batch mode: convert all .jpg/.jpeg/.png images in the input_path directory",
    )

    return parser.parse_args()
