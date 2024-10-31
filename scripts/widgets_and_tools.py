from os.path import commonprefix

import ipywidgets as widgets
import pandas as pd
from IPython.display import display

QC_flags = {
    "NO_QUALITY_CONTROL": 0,
    "GOOD": 1,
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
}


def get_common_pre_suf_fix(input_list, mode="prefix"):
    if mode == "suffix":
        input_list = [s[::-1] for s in input_list]
    out = commonprefix(input_list)
    out = [out, out[::-1]][mode == "suffix"]

    return out


def strip_common_pre_and_suffix(input_list):
    prefix = get_common_pre_suf_fix(input_list, mode="prefix")
    suffix = get_common_pre_suf_fix(input_list, mode="suffix")
    out = [s.lstrip(prefix).rstrip(suffix) for s in input_list]
    return out


# Multi-Select
def create_group_widget(df: pd.DataFrame, key_group: str = "group") -> widgets.Select:
    group_widget = widgets.Select(
        options=sorted(df[key_group].unique()),
        description="Group",
    )
    return group_widget


def create_casts_widget() -> widgets.SelectMultiple:
    casts_widget = widgets.SelectMultiple(
        description="Casts",
    )
    return casts_widget


def create_qc_widget() -> widgets.Dropdown:
    qc_widget = widgets.Dropdown(
        options=QC_flags.keys(),
    )
    return qc_widget


def update_casts(group, widget_group, widget_casts, df):
    widget_casts.options = sorted(
        list(df.loc[df["group"] == widget_group.value, "CASTS"].unique())
    )


def update_flag_widget(casts, widget_group, widget_casts, widget_qc, df, df_source):
    # casts_widget.observe(update_flag_widget, names="value")
    # current_flag_value = df_profile.loc[df_profile["CASTS"].isin(casts_widget.value) and df_profile["group"] == group_widget.value, "QC_cast_flag"]
    # qc_widget.value = list(QC_flags.keys())[list(QC_flags.values()).index(current_flag_value)][0]
    current_flag_value = df.loc[
        df_source["CASTS"].isin(widget_casts.value) and df_source["group"] == widget_group.value,
        "QC_cast_flag",
    ]
    widget_qc.value = list(QC_flags.keys())[
        list(QC_flags.values()).index(current_flag_value)
    ][0]


def update_flag(flag, widget_group, widget_casts, widget_qc, df, df_source):
    df.loc[
        (df_source["CASTS"].isin(widget_casts.value)) & (df_source["group"] == widget_group.value),
        "QC_cast_flag",
    ] = QC_flags[widget_qc.value]


def display_flagging_widgets(df: pd.DataFrame, df_source: pd.DataFrame) -> None:
    group_widget = create_group_widget(df=df_source)
    casts_widget = create_casts_widget()
    qc_widget = create_qc_widget()

    group_widget.observe(
        lambda group: update_casts(
            group, widget_group=group_widget, widget_casts=casts_widget, df=df_source
        ),
        names="value",
    )
    casts_widget.observe(
        lambda cast: update_flag_widget(
            cast, widget_group=group_widget, widget_casts=casts_widget, widget_qc=qc_widget, df=df, df_source=df_source
        ),
        names="value",
    )
    qc_widget.observe(
        lambda flag: update_flag(flag, widget_group=group_widget, widget_casts=casts_widget, widget_qc=qc_widget, df=df, df_source=df_source),
        names="value",
    )

    display(group_widget, casts_widget, qc_widget)
