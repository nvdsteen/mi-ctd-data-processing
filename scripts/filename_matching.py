from pathlib import Path
import pandas as pd


def main():
    folder = Path("2024_01/raw_files")
    files = []
    for fi in folder.iterdir():
        files.append((fi.stem, fi.suffix, fi.stem.lower()))
    df = pd.DataFrame(files, columns=["basename", "suffix", "basename_lower"])
    pass


if __name__ == "__main__":
    main()
