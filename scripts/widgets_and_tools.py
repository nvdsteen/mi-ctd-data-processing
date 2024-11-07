import re
from os.path import commonprefix

import ipywidgets as widgets
import pandas as pd
from IPython.display import display

QC_flags = {
    "NO_QUALITY_CONTROL": 0,
    # "GOOD": 1,
    "PROBABLY_GOOD": 2,
    "PROBABLY_BAD": 3,
    #   "CHANGED": 5,
    #   "BELOW_DETECTION": 6,
    #   "IN_EXCESS": 7,
    #   "INTERPOLATED": 8,
    #   "MISSING": 9,
    #   "PHENOMENON_UNCERTAIN": "A",
    #   "NOMINAL": "B",
    #   "BELOW_LIMIT_OF_QUANTIFICATION": "Q",
    "BAD": 4,
    #   "MIXED": None,
    "": 0,
}

column_qc_flag = "QC_cast_flag"
column_group = "group"
column_casts = "CASTS"


def get_common_pre_suf_fix(input_list, mode="prefix"):
    if mode == "suffix":
        input_list = [s[::-1] for s in input_list]
    out = commonprefix(input_list)
    out = [out, out[::-1]][mode == "suffix"]

    return out


def strip_common_pre_and_suffix(input_list):
    prefix = get_common_pre_suf_fix(input_list, mode="prefix")
    suffix = get_common_pre_suf_fix(input_list, mode="suffix")
    out = [s.replace(prefix, "", 1).rsplit(suffix)[0] for s in input_list]
    return out


# Multi-Select
def create_group_widget(
    df: pd.DataFrame, key_group: str = column_group
) -> widgets.Select:
    group_widget = widgets.Select(
        options=[""] + sorted(df[key_group].unique()),
        description="Group",
    )
    group_widget.value = ""
    return group_widget


def create_casts_widget(init_options: list = []) -> widgets.SelectMultiple:
    casts_widget = widgets.SelectMultiple(
        description="Casts",
        options=init_options,
    )
    return casts_widget


def create_qc_widget() -> widgets.Dropdown:
    qc_widget = widgets.Dropdown(
        description="Flags",
        options=QC_flags.keys(),
    )
    return qc_widget


def update_casts(group, widget_group, widget_casts, df):
    widget_casts.options = sorted(
        list(df.loc[df[column_group] == widget_group.value, column_casts].unique())
    )


def update_flag_widget(casts, widget_group, widget_casts, widget_qc, df):
    current_flags = list(
        df.loc[
            (df[column_group] == widget_group.value)
            & (df[column_casts].isin(widget_casts.value)),
            column_qc_flag,
        ].unique()
    )
    current_flag = 0
    current_flag_value = list(QC_flags.keys())[
        list(QC_flags.values()).index(current_flag)
    ]
    if len(current_flags) == 1:
        current_flag = current_flags[0]
        current_flag_value = list(QC_flags.keys())[
            list(QC_flags.values()).index(current_flag)
        ]

    else:
        current_flag_value = ""
    widget_qc.value = current_flag_value


def update_flag(flag, widget_group, widget_casts, widget_qc, df, write_to):
    df.loc[
        (df[column_casts].isin(widget_casts.value))
        & (df[column_group] == widget_group.value),
        column_qc_flag,
    ] = QC_flags[widget_qc.value]
    if write_to:
        df.to_csv(write_to, index=False)
        # df.to_csv(write_to, index=False, usecols=set(df.columns).difference([column_group, column_casts]))


def add_group_casts_columns_to_df(
    df: pd.DataFrame, base_column: str = "profile"
) -> pd.DataFrame:
    df[column_group] = strip_common_pre_and_suffix(list(df[base_column]))
    df[column_group] = df[column_group].str.split(r"(?i)CAST", n=1).str[0].str.strip()

    df[column_casts] = pd.Series(
        strip_common_pre_and_suffix(list(df["profile"]))
    ).str.split(r"(?i)CAST", n=1, expand=True)[1]

    # df.loc[df[column_casts].isna(), column_casts] = df.loc[df[column_casts].isna(), column_group]
    df[column_casts] = df[column_casts].fillna(df[column_group])

    df[column_casts] = df[column_casts].str.strip()

    print(f"{type(df)}")
    return df


def display_flagging_widgets(
    df: pd.DataFrame, write_to: str | None = None, base_column: str = "profile"
) -> dict[str, widgets.widgets.widget.Widget]:
    df = add_group_casts_columns_to_df(df, base_column=base_column)
    if column_qc_flag not in df.columns:
        df[column_qc_flag] = 0
        # df.to_csv(write_to, index=False, usecols=set(df.columns).difference([column_group, column_casts]))
        df.to_csv(write_to, index=False)
    group_widget = create_group_widget(df=df)
    init_options_casts = sorted(list(df.loc[df[column_group] == group_widget.value, column_casts].unique()))  # type: ignore
    casts_widget = create_casts_widget(init_options=init_options_casts)
    qc_widget = create_qc_widget()

    group_widget.observe(
        lambda group: update_casts(
            group, widget_group=group_widget, widget_casts=casts_widget, df=df
        ),
        names="value",
    )
    casts_widget.observe(
        lambda cast: update_flag_widget(
            cast,
            widget_group=group_widget,
            widget_casts=casts_widget,
            widget_qc=qc_widget,
            df=df,
        ),
        names="value",
    )
    qc_widget.observe(
        lambda flag: update_flag(
            flag,
            widget_group=group_widget,
            widget_casts=casts_widget,
            widget_qc=qc_widget,
            df=df,
            write_to=write_to,
        ),
        names="value",
    )

    display(group_widget, casts_widget, qc_widget)
    return {"group": group_widget, "casts": casts_widget, "flag": qc_widget}
