from pathlib import Path
import pandas as pd
# import openpyxl
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
    filename: str | Path, search_path: str | Path, searched_extension: str, return_full_path: bool=False
) -> str:
    pattern = re.compile(Path(filename).stem + f"{searched_extension}", re.IGNORECASE)
    files = [f for f in Path(search_path).rglob("*") if pattern.match(f.name)]
    assert len(files) <= 1
    if len(files) == 0:
        return ""

    if return_full_path:
        return files[0].as_posix()
    return files[0].name


def match_stem_caseinsensitive_lists(matching: list[str], input: list[str]):
    matched = []
    for mi in matching:
        pattern = re.compile(mi, re.IGNORECASE)
        matched += [fi for fi in input if pattern.match(fi)]
    return matched


def adjust_worksheet_columns_width(worksheet):
    for col in worksheet.columns:
        max_length = 0
        column_name = col[0].column_letter  # Get the column name
        for cell in col:
            try:  # Necessary to avoid error on empty cells
                cell_length = len(str(cell.value))
                if str(cell.value).startswith("=HYPERLINK"):
                    cell_length = len(str(cell.value).rsplit(",")[-1].strip('"'))
                if cell_length > max_length:
                    max_length = cell_length
            except:
                pass
        adjusted_width = (max_length + 2) * 1.2
        worksheet.column_dimensions[column_name].width = adjusted_width


def main():
    # path_elements = ["Documents", "RBINS", "Onedrive", "CTD_testing"]
    # folder = Path().home().joinpath(*path_elements)
    # out = Path().home().joinpath(*path_elements).joinpath("mismatched_filenames")
    # if not out.exists():
    #     out.mkdir()

    # raw_folders = folder.rglob("raw_files")
    # out_overview = out.parent.joinpath("overview.xlsx")

    # columns = [".xmlcon", ".hex", ".bl", ".mrk", ".hdr", ".btl", ".cnv"]
    # skip_columns = [".cnv", ".btl"]

    # columns = [ci for ci in columns if ci not in skip_columns]

    # content_overview = []
    # for di in raw_folders:
    #     di_name = di.parent.name
    #     dfi = get_df_files(di)

    #     relevant_columns = sorted(
    #         list(set(dfi.columns).intersection(columns)), key=lambda i: columns.index(i)
    #     )
    #     additional_columns = set(dfi.columns).difference(relevant_columns)

    #     output_file = out.joinpath(di_name + "_mismatching_files.xlsx")
    #     rows_with_mismatch = dfi[relevant_columns].isna().any(axis=1)
    #     dfi_mismatch = dfi.loc[rows_with_mismatch, relevant_columns]
    #     dfi_mismatch = dfi_mismatch.dropna(axis=0, how="all")
    #     btl_in_folder = ".btl" in relevant_columns

    #     if rows_with_mismatch.any() or btl_in_folder:
    #         sheet_name = "Mismatching filenames"
    #         with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
    #             dfi_mismatch.to_excel(
    #                 writer, sheet_name=sheet_name, startrow=3, index=False
    #             )

    #         wb = openpyxl.load_workbook(output_file)
    #         ws = wb[sheet_name]
    #         ws["A1"] = f"Addition columns:"
    #         ws["B1"] = f"{', '.join(additional_columns)}"
    #         ws["A2"] = f".btl files in raw_files folder:"
    #         ws["B2"] = f"{'.btl' in relevant_columns}"

    #         adjust_worksheet_columns_width(worksheet=ws)
    #         wb.save(output_file)

    #         content_overview += [
    #             (
    #                 di_name,
    #                 f'=HYPERLINK("{output_file.relative_to(out_overview.parent).as_posix()}", "{di_name}"',
    #             )
    #         ]
    #     else:
    #         content_overview += [(di_name, "")]
    # df_overview = pd.DataFrame(
    #     content_overview, columns=["Dataset", "Link"]
    # ).sort_values("Dataset")
    # sheet_name_overview = "Filename mismatching datasets"
    # with pd.ExcelWriter(out_overview, engine="openpyxl") as writer:
    #     df_overview.to_excel(writer, sheet_name=sheet_name_overview, index=False)
    # wb = openpyxl.load_workbook(out_overview)
    # ws = wb[sheet_name_overview]
    # adjust_worksheet_columns_width(worksheet=ws)
    # wb.save(out_overview)


if __name__ == "__main__":
    main()
