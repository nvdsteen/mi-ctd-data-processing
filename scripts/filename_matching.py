from pathlib import Path
import pandas as pd
import re


def get_df_files(folder: Path | str) -> pd.DataFrame:
    files = []
    for fi in Path(folder).iterdir():
        files.append((fi.stem, fi.suffix.lower(), fi.stem.lower()))
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


def match_stem_caseinsensitive(
    filename: str | Path, search_path: str | Path, searched_extension: str
) -> str:
    pattern = re.compile(Path(filename).stem + f"{searched_extension}", re.IGNORECASE)
    files = [f for f in Path(search_path).rglob("*") if pattern.match(f.name)]
    assert len(files) == 1
    return files[0].name


def main():
    # folder = Path("2024_01/raw_files")
    folder = Path(
        # "/home/nvds/Documents/RBINS/Onedrive/CTD_testing/Data2022/2022_09a/raw_files"
        "/home/nvadmin/Documents/IrishMarineInstitute/mi-ctd-data-processing/CTD_data_renamed"
    )
    out = Path(
        "/home/nvadmin/Documents/IrishMarineInstitute/mi-ctd-data-processing/CTD_data_renamed/mismatched_filenames/"
    )
    raw_folders = folder.rglob("raw_files")
    out_overview = out.parent.joinpath("overview.xslx")

    columns = [".xmlcon", ".hex", ".bl", ".mrk", ".hdr", ".btl", ".cnv"]

    content_overview = []
    for di in raw_folders:
        di_name = di.parent.name
        dfi = get_df_files(di)

        relevant_columns = sorted(
            list(set(dfi.columns).intersection(columns)), key=lambda i: columns.index(i)
        )
        additional_columns = set(dfi.columns).difference(relevant_columns)

        output_file = out.joinpath(di_name + "_mismatching_files.csv")
        dfi_mismatch = dfi[dfi[relevant_columns].isna().any(axis=1)]

        # dfi_mismatch.to_csv(output_file)

        template = ""
        if additional_columns:
            template += f"Addition columns: {', '.join(additional_columns)}\n"
        if ".btl" in relevant_columns:
            template += f"{di_name} has .btl files in raw_files folder.\n"

        template += "{}"

        if template.format("") or not dfi_mismatch.empty:
            with open(output_file, "w+") as fi:
                fi.write(template.format(dfi_mismatch.to_csv(index=True)))
                # content_overview += [(di_name, f"=HYPERLINK(\"{output_file.as_posix()}\", \"{di_name}\"")]
                content_overview += [(di_name, f"=HYPERLINK(\"{output_file.relative_to(out_overview.parent).as_posix()}\", \"{di_name}\"")]
    pd.DataFrame(content_overview, columns=["Dataset", "Link"]).to_excel(out_overview)


if __name__ == "__main__":
    main()
