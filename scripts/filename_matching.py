from pathlib import Path
import pandas as pd
import re


def get_df_files(folder: Path | str) -> pd.DataFrame:
    files = []
    for fi in Path(folder).iterdir():
        files.append((fi.stem, fi.suffix, fi.stem.lower()))
    df = pd.DataFrame(files, columns=["basename", "suffix", "basename_lower"])
    df_pivot = df.pivot(index="basename_lower", columns=["suffix"], values="basename")
    return df_pivot


def replace_extension(file: Path | str, ext_in, ext_out) -> str:
    filename = Path(file).name
    file = Path(file)
    if file.suffix.lower() == ext_in:
        return Path(file).with_suffix(ext_out).as_posix()
    else:
        return file.as_posix()

        
def match_stem_caseinsensitive(filename: str | Path, search_path: str | Path, searched_extension: str) -> str:
    pattern = re.compile(Path(filename).stem + f"{searched_extension}", re.IGNORECASE)
    files = [f for f in Path(search_path).rglob('*') if pattern.match(f.name)]
    assert len(files) == 1
    return files[0].name



def main():
    # folder = Path("2024_01/raw_files")
    folder = Path(
        "/home/nvds/Documents/RBINS/Onedrive/CTD_testing/Data2022/2022_09a/raw_files"
    )
    df_pivot = get_df_files(folder)
    pass


if __name__ == "__main__":
    main()
