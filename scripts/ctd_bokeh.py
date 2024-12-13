# -*- coding: utf-8 -*-
"""
Created on Thu Mar 14 09:41:32 2024

@author: dosullivan1
"""
# import packages
import os
from itertools import cycle
from bokeh.models import (
    ColumnDataSource,
    CategoricalColorMapper,
    DataRange1d,
    ColorBar,
    Select,
    Button,
    Slider,
    Legend,
    RadioGroup,
    BoxAnnotation,
    Label,
    LegendItem,
)
from bokeh.layouts import row, column, Spacer, gridplot
from bokeh.plotting import figure, save, output_file
from bokeh.transform import linear_cmap
from bokeh.palettes import Viridis256, Category10

# Import bespoke functions
import scripts.calculations as calculations
from scripts.water_mass_configuration import patch_dict, box_dict


# %%
def update_button_attr(button_name, disbld, b_type):
    button_name.disabled = disbld
    button_name.button_type = b_type


# %%
class bokeh_layout:
    prDM_threshold = 1

    def __init__(self, profile_data, pump_data, output_path, downcast_data):

        # Define variables
        self.profile_data = profile_data
        self.pump_data = pump_data
        self.output_path = output_path
        self.downcast_data = downcast_data
        self.oxy_align_default = 2

        if "profile" in profile_data.columns:
            self.profile_list = self.profile_data["profile"].unique().tolist()
        elif "CTD number" in profile_data.columns:
            self.profile_list = self.profile_data["CTD number"].unique().tolist()
        else:
            self.profile_list = []
        self.param_list = self.profile_data.columns.tolist()

        key_turbidity = "TurbidityMeter_0"
        if key_turbidity not in profile_data.columns:
            self.profile_data[key_turbidity] = float("nan")

        # Define widgets
        # Profile allows users to select the profile they want to view
        self.profile = Select(options=self.profile_list, value=self.profile_list[0])
        # Next profile allows users to click through to the next cast of the cruise
        self.next_profile = Button(
            label=">",
            button_type="primary",
            width=50,
            disabled=False,
        )
        # Previous profile allows users to click through to the previous cast of the cruise
        self.prev_profile = Button(
            label="<",
            button_type="default",
            width=50,
            disabled=True,
        )
        self.o2adv1 = Slider(
            title="Primary oxygen sensor alignment [s]",
            start=-12,
            end=12,
            step=1,
            value=int(self.oxy_align_default),
        )
        self.o2adv2 = Slider(
            title="Secondary oxygen sensor alignment [s]",
            start=-12,
            end=12,
            step=1,
            value=int(self.oxy_align_default),
        )
        # Cast start allows a user to define when the cast started
        self.cast_start = Button(
            label="Set cast start",
            button_type="primary",
            width=200,
            disabled=False,
        )

    # Define functions associated with widgets
    def next_pf(self):
        # Update to next profile in the list
        pf = self.profile_list.index(self.profile.value)
        self.profile.value = self.profile_list[pf + 1]
        self.update_button_avail()

    def prev_pf(self):
        # Update to previous profile in the list
        pf = self.profile_list.index(self.profile.value)
        self.profile.value = self.profile_list[pf - 1]
        self.update_button_avail()

    def update_button_avail(self):
        # Toggle availability of previous and next profile buttons if first or last profile selected
        if self.profile_list.index(self.profile.value) + 1 == len(self.profile_list):
            update_button_attr(self.next_profile, True, "default")
            update_button_attr(self.prev_profile, False, "primary")
        elif self.profile_list.index(self.profile.value) == 0:
            update_button_attr(self.next_profile, False, "primary")
            update_button_attr(self.prev_profile, True, "default")
        else:
            update_button_attr(self.next_profile, False, "primary")
            update_button_attr(self.prev_profile, False, "primary")

    def screen_html(self):
        output_file(
            os.path.join(
                self.output_path, "plots", "%s_plots.html" % self.profile.value
            )
        )
        save(self.visualisation_layout)

    def surface_soak(self):
        # Define surface soak functionality
        # Surface Soak data and manipulation
        # Define the ColumnDataSource for the surface soak screening plot
        self.soak_df = self.profile_data[
            (self.profile_data["profile"] == self.profile.value)
            & (self.profile_data["prDM"] < 20)
            & (self.profile_data["cast"] == "D")
        ].copy(deep=True)
        self.soak_df["pumps_txt"] = "Off"
        self.soak_df.loc[self.soak_df["pumps"] == 1, "pumps_txt"] = "On"
        self.col_src_surface_soak = ColumnDataSource(self.soak_df)

        # Time pump came on for each casts
        pump_time_on = self.pump_data[
            self.pump_data["profile"] == self.profile.value
        ].copy(deep=True)
        self.col_src_pump_time_on = ColumnDataSource(pump_time_on)

        # Oxygen channel updates
        if "sbeox0Mm/L" in self.param_list:
            # Define the ColumnDataSource for the oxygen alignment plot 1
            oxy1_df = self.profile_data[
                (self.profile_data["profile"] == self.profile.value)
                & (self.profile_data["prDM"] > bokeh_layout.prDM_threshold)
            ][["t090C", "sbeox0Mm/L"]]
            oxy1_df["sbeox0Mm/L"] = oxy1_df["sbeox0Mm/L"].shift(periods=self.o2adv1.value * -2)  # type: ignore
            self.src_oxy1 = ColumnDataSource(oxy1_df)
        if "sbeox1Mm/L" in self.param_list:
            # Define the ColumnDataSource for the oxygen alignment plot 2
            oxy2_df = self.profile_data[
                (self.profile_data["profile"] == self.profile.value)
                & (self.profile_data["prDM"] > bokeh_layout.prDM_threshold)
            ][["t190C", "sbeox1Mm/L"]]
            oxy2_df["sbeox1Mm/L"] = oxy2_df["sbeox1Mm/L"].shift(periods=self.o2adv2.value * -2)  # type: ignore
            self.src_oxy2 = ColumnDataSource(oxy2_df)

        # Set up pressure vs time plot settings
        pumps_factors = ["Off", "On"]
        pumps_palette = ["yellow", "blue"]
        pump_color_mapper = CategoricalColorMapper(
            factors=pumps_factors,
            palette=pumps_palette,
        )
        pump_color_dict = dict(field="pumps_txt", transform=pump_color_mapper)

        # Set up plots
        surface_soak_plot = figure(
            width=500,
            height=500,
            x_axis_label="Cycles",
            y_axis_label="prDM",
            x_axis_location="below",
            tools="pan,wheel_zoom,box_zoom,tap,reset",
            toolbar_location="above",
            output_backend="webgl",
        )
        surface_soak_plot.add_layout(Legend(orientation="horizontal"), "below")
        surface_soak_plot.y_range.flipped = True
        # Add data to plot
        surface_soak_plot.scatter(
            "Cycles",
            "prDM",
            source=self.col_src_surface_soak,
            color=pump_color_dict,
            fill_alpha=0.2,
            size=5,
            # legend_label='pumps_txt',
        )
        surface_soak_plot.scatter(
            "Cycles",
            "prDM",
            source=self.col_src_pump_time_on,
            color="red",
            fill_alpha=0.5,
            size=15,
        )
        self.surface_soak_plot = surface_soak_plot

        if "sbeox0Mm/L" in self.param_list:
            # Set up oxygen vs temperature plot settings
            surface_soak_oxy_temp_plot = figure(
                width=500,
                height=500,
                x_axis_label="sbeox0Mm/L",
                y_axis_label="t090C",
                x_axis_location="below",
                tools="pan,wheel_zoom,box_zoom,reset",
                toolbar_location="above",
                output_backend="webgl",
            )
            # Add data to plot
            surface_soak_oxy_temp_plot.line(
                "sbeox0Mm/L",
                "t090C",
                source=self.src_oxy1,
                color="blue",
                line_width=2,
            )
            self.surface_soak_oxy_temp_plot = surface_soak_oxy_temp_plot

        if "sbeox1Mm/L" in self.param_list:
            # Set up oxygen vs temperature plot settings
            surface_soak_oxy_temp2_plot = figure(
                width=500,
                height=500,
                x_axis_label="sbeox1Mm/L",
                y_axis_label="t190C",
                x_axis_location="below",
                tools="pan,wheel_zoom,box_zoom,reset",
                toolbar_location="above",
                output_backend="webgl",
            )
            # Add data to plot
            surface_soak_oxy_temp2_plot.line(
                "sbeox1Mm/L",
                "t190C",
                source=self.src_oxy2,
                color="blue",
                line_width=2,
            )
            self.surface_soak_oxy_temp2_plot = surface_soak_oxy_temp2_plot

    # Add update functions
    def update_surface_soak_plot(self, attr, old, new):
        soak_data_updated = self.profile_data[
            (self.profile_data["profile"] == self.profile.value)
            & (self.profile_data["prDM"] < 20)
            & (self.profile_data["cast"] == "D")
        ].copy(deep=True)
        soak_data_updated["pumps_txt"] = "Off"
        soak_data_updated.loc[soak_data_updated["pumps"] == 1, "pumps_txt"] = "On"
        src_updated = ColumnDataSource(soak_data_updated)
        self.col_src_surface_soak.data.update(src_updated.data)
        self.update_button_avail()

        # Update plot for pump dataframe source
        pump_time_updated = self.pump_data[
            self.pump_data["profile"] == self.profile.value
        ].copy(deep=True)
        col_src_pump_time_updated = ColumnDataSource(pump_time_updated)
        self.col_src_pump_time_on.data.update(col_src_pump_time_updated.data)

        # Oxygen channel updates
        if "sbeox0Mm/L" in self.param_list:
            # Update source for p1
            oxy1_df_updated = self.profile_data[
                (self.profile_data["profile"] == self.profile.value)
                & (self.profile_data["prDM"] > bokeh_layout.prDM_threshold)
            ][["t090C", "sbeox0Mm/L"]]
            oxy1_df_updated["sbeox0Mm/L"] = oxy1_df_updated["sbeox0Mm/L"].shift(periods=self.o2adv1.value * -2)  # type: ignore
            src_oxy1_updated = ColumnDataSource(oxy1_df_updated)
            self.src_oxy1.data.update(src_oxy1_updated.data)

        if "sbeox1Mm/L" in self.param_list:
            # Update source for p2
            oxy2_df_updated = self.profile_data[
                (self.profile_data["profile"] == self.profile.value)
                & (self.profile_data["prDM"] > bokeh_layout.prDM_threshold)
            ][["t190C", "sbeox1Mm/L"]]
            oxy2_df_updated["sbeox1Mm/L"] = oxy2_df_updated["sbeox1Mm/L"].shift(periods=self.o2adv2.value * -2)  # type: ignore
            src_oxy2_updated = ColumnDataSource(oxy2_df_updated)
            self.src_oxy2.data.update(src_oxy2_updated.data)

    def update_cast_start(self):
        # Identify selected point
        point = self.col_src_surface_soak.selected.indices  # type: ignore
        # Check only one point selected
        if len(point) != 1:
            print("Please select only 1 point")
        else:
            # Identify updated values
            icycles = self.col_src_surface_soak.data["Cycles"][point[0]]
            itimeS = self.col_src_surface_soak.data["timeS"][point[0]]
            iprDM = self.col_src_surface_soak.data["prDM"][point[0]]
            # Update pumpdf dataframe
            self.pump_data.loc[
                self.pump_data["profile"] == self.profile.value, "Cycles"
            ] = icycles
            self.pump_data.loc[
                self.pump_data["profile"] == self.profile.value, "timeS"
            ] = itimeS
            self.pump_data.loc[
                self.pump_data["profile"] == self.profile.value, "prDM"
            ] = iprDM

            # Save update to file
            pump_csv = os.path.join(self.output_path, "pump_on_time.csv")
            self.pump_data.to_csv(pump_csv, index=False)

            # update plot for pump dataframe source
            self.pump_on_time_updated = self.pump_data[
                self.pump_data["profile"] == self.profile.value
            ].copy(deep=True)
            src_a_updated = ColumnDataSource(self.pump_on_time_updated)
            self.col_src_pump_time_on.data.update(src_a_updated.data)

    def surface_soak_screening(self, doc):

        self.surface_soak()

        #  Link update functions to interactive widgets
        self.profile.on_change("value", self.update_surface_soak_plot)
        self.next_profile.on_click(self.next_pf)
        self.prev_profile.on_click(self.prev_pf)
        self.cast_start.on_click(self.update_cast_start)

        # Following functions depend on the presence of oxygen sensors
        if "sbeox0Mm/L" in self.param_list:
            self.o2adv1.on_change("value_throttled", self.update_surface_soak_plot)
        if "sbeox1Mm/L" in self.param_list:
            self.o2adv2.on_change("value_throttled", self.update_surface_soak_plot)

        # Define dashboard layout depending on how many oxygen sensors are present
        if "sbeox0Mm/L" not in self.param_list:
            layout = column(
                row(
                    Spacer(width=40),
                    self.prev_profile,
                    Spacer(width=50),
                    self.profile,
                    self.next_profile,
                ),
                row(self.cast_start),
                row(self.surface_soak_plot),
            )

        if "sbeox0Mm/L" in self.param_list:
            layout = column(
                row(
                    Spacer(width=40),
                    self.prev_profile,
                    Spacer(width=50),
                    self.profile,
                    self.next_profile,
                    Spacer(width=50),
                    Spacer(width=50),
                    self.o2adv1,
                ),
                row(self.cast_start),
                row(self.surface_soak_plot, self.surface_soak_oxy_temp_plot),
            )

        if "sbeox1Mm/L" in self.param_list:
            layout = column(
                row(
                    Spacer(width=40),
                    self.prev_profile,
                    Spacer(width=50),
                    self.profile,
                    self.next_profile,
                    Spacer(width=50),
                    Spacer(width=50),
                    self.o2adv1,
                    Spacer(width=175),
                    self.o2adv2,
                ),
                row(self.cast_start),
                row(
                    self.surface_soak_plot,
                    self.surface_soak_oxy_temp_plot,
                    self.surface_soak_oxy_temp2_plot,
                ),
            )
        # Add the layout to the document
        doc.add_root(layout)

    def heave(self):
        # Set heave plot widgets
        self.profile.value = self.profile_list[0]

        # Define the ColumnDataSource for the surface sock screening plot
        heave_df = self.downcast_data[
            self.downcast_data["CTD number"] == self.profile.value
        ].copy(deep=True)
        self.col_src_heave = ColumnDataSource(heave_df)

        # Set the QC flag colour mapping
        flag_factors = ["0", "1", "3", "4"]
        flag_palette = ["blue", "green", "orange", "red"]
        heave_color_mapper = CategoricalColorMapper(
            factors=flag_factors,
            palette=flag_palette,
        )
        heave_color_dict = dict(field="prDM_QC", transform=heave_color_mapper)

        # Set the plot tooltips
        plot_tooltips = [
            ("velocity", "@CTDvel"),
            ("QC", "@prDM_QC"),
        ]

        # Set up pressure vs time plot settings
        pressure_time_plot = figure(
            width=500,
            height=500,
            x_axis_label="timeS",
            y_axis_label="prDM",
            x_axis_location="below",
            tools="pan,wheel_zoom,box_zoom,box_select,tap,reset",
            toolbar_location="above",
            tooltips=plot_tooltips,
            output_backend="webgl",
        )
        pressure_time_plot.y_range.flipped = True
        # Add data to plot
        pressure_time_plot.scatter(
            "timeS",
            "prDM",
            source=self.col_src_heave,
            color=heave_color_dict,
            fill_alpha=0.2,
            size=5,
        )
        self.pressure_time_plot = pressure_time_plot

        # Set up pressure vs temperature plot settings
        pressure_temperature_plot = figure(
            width=500,
            height=500,
            x_axis_label="t090C",
            y_axis_label="prDM",
            x_axis_location="below",
            y_range=pressure_time_plot.y_range,
            tools="pan,wheel_zoom,box_zoom,box_select,tap,reset",
            toolbar_location="above",
            tooltips=plot_tooltips,
            output_backend="webgl",
        )

        # Add data to plot
        pressure_temperature_plot.scatter(
            "t090C",
            "prDM",
            source=self.col_src_heave,
            color=heave_color_dict,
            fill_alpha=0.2,
            size=5,
        )
        self.pressure_temperature_plot = pressure_temperature_plot

        # Set up pressure vs salinity plot settings
        pressure_salinity_plot = figure(
            width=500,
            height=500,
            x_axis_label="sal00",
            y_axis_label="prDM",
            x_axis_location="below",
            y_range=pressure_time_plot.y_range,
            tools="pan,wheel_zoom,box_zoom,box_select,tap,reset",
            toolbar_location="above",
            tooltips=plot_tooltips,
            output_backend="webgl",
        )
        pressure_salinity_plot.y_range.flipped = True
        # Add data to plot
        pressure_salinity_plot.scatter(
            "sal00",
            "prDM",
            source=self.col_src_heave,
            color=heave_color_dict,
            fill_alpha=0.2,
            size=5,
        )
        self.pressure_salinity_plot = pressure_salinity_plot

    def update_heave_plot(self, attr, old, new):
        # Heave update function
        df_updated = self.downcast_data[
            self.downcast_data["CTD number"] == self.profile.value
        ].copy(deep=True)
        col_src_heave_updated = ColumnDataSource(df_updated)
        self.col_src_heave.data.update(col_src_heave_updated.data)

    def heave_screening(self, doc):

        self.heave()
        self.profile.on_change("value", self.update_heave_plot)
        self.next_profile.on_click(self.next_pf)
        self.prev_profile.on_click(self.prev_pf)

        # Define dashboard layout
        layout = column(
            row(
                Spacer(width=40),
                self.prev_profile,
                Spacer(width=50),
                self.profile,
                self.next_profile,
                Spacer(width=50),
            ),
            row(
                self.pressure_time_plot,
                self.pressure_temperature_plot,
                self.pressure_salinity_plot,
            ),
        )

        doc.add_root(layout)

    def get_suite_dict(self):
        sensor_suffix = "0" if self.sensor_suite.active == 0 else "1"
        suite_dict = {
            "CTD number": "CTD number",
            "Latitude [degrees_north]": "Latitude [degrees_north]",
            "Longitude [degrees_east]": "Longitude [degrees_east]",
            "Eastings": "Eastings",
            "Northings": "Northings",
            "Date": "CTD_start",
            "depth": "depSM",
            "pres": "prDM",
            "TurbidityMeter_0": "TurbidityMeter_0",
            "temp": f"t{sensor_suffix}90C",
            "cond": f"c{sensor_suffix}S/m",
            "sal": f"sal{sensor_suffix}0",
            "potemp": f"potemp{sensor_suffix}90C",
            "sigma-theta": f"sigma-theta{sensor_suffix}0",
            "svel": f"svel{sensor_suffix}0",
            "oxy_conc": f"sbeox{sensor_suffix}Mm/L",
            "oxy_sat": f"sbeox{sensor_suffix}PS",
        }
        return suite_dict

    @staticmethod
    def get_fig_fct_depth(
        x_axis_label,
        y_axis_label="Depth [m]",
        x_axis_location="above",
        tools="pan,wheel_zoom,box_zoom,box_select,tap,reset",
        toolbar_location="above",
        output_backend="webgl",
    ):
        fig_out = figure(
            x_axis_label=x_axis_label,
            y_axis_label=y_axis_label,
            x_axis_location=x_axis_location,
            tools=tools,
            toolbar_location=toolbar_location,
            output_backend=output_backend,
        )
        return fig_out

    @staticmethod
    def scatter_fct_depth(fig, x, source, color, fill_alpha=0.2, size=5):
        si = fig.scatter(
            x, "depth", source=source, color=color, fill_alpha=fill_alpha, size=size
        )
        return si

    @staticmethod
    def line_fct_depth(fig, x, source, color, line_alpha=1, line_width=0.5):
        li = fig.line(
            x,
            "depth",
            source=source,
            color=color,
            line_alpha=line_alpha,
            line_width=line_width,
        )
        return li

    def bin_data(self):
        # Set heave plot widgets
        self.profile.value = self.profile_list[0]

        self.screen_print = Button(
            label="Save as HTML",
            button_type="default",
            width=50,
            disabled=False,
        )
        self.sensor_suite = RadioGroup(
            labels=["primary", "secondary"],
            active=0,
        )
        self.x_axis_filter = Select(
            options=["Longitude [degrees_east]", "Latitude [degrees_north]", "Date"],
            value="Longitude [degrees_east]",
        )

        # Define the ColumnDataSource for the profile plots

        self.suite = list(self.get_suite_dict().values())

        # self.renamed = list(suite_dict.keys())

        df_st = self.profile_data[
            self.profile_data["CTD number"] == self.profile.value
        ][self.suite].copy(deep=True)
        df_st = df_st.rename(columns={v: k for k, v in self.get_suite_dict().items()})

        self.col_src_bin = ColumnDataSource(df_st)
        self.col_src_metadata = ColumnDataSource(
            self.profile_data[["CTD number", "Eastings", "Northings"]].drop_duplicates()
        )

        # Define ColumnDataSource for T-S plot
        df_ts = self.profile_data[self.suite].copy(deep=True)
        df_ts = df_ts.rename(columns={v: k for k, v in self.get_suite_dict().items()})
        df_ts["SectionX"] = df_ts[self.x_axis_filter.value]
        self.col_src_ts = ColumnDataSource(df_ts)

        # Map plot
        survey_map = figure(
            tools="pan,wheel_zoom,box_zoom,box_select,tap,reset",
            x_axis_type="mercator",
            y_axis_type="mercator",
            width=300,
            height=300,
            toolbar_location="above",
            output_backend="webgl",
        )
        survey_map.add_tile("CartoDB Positron", retina=True)
        survey_map.xaxis.axis_label = "Longitude [degrees E]"
        survey_map.yaxis.axis_label = "Latitude [degrees N]"

        survey_map.scatter(
            x="Eastings",
            y="Northings",
            size=5,
            fill_color="blue",
            fill_alpha=0.5,
            source=self.col_src_ts,
        )

        survey_map.scatter(
            x="Eastings",
            y="Northings",
            size=5,
            fill_color="red",
            fill_alpha=1.0,
            selection_fill_color="red",
            source=self.col_src_bin,
        )

        self.survey_map = survey_map

        # Set up depth vs temperature plot settings
        depth_temperature = self.get_fig_fct_depth(x_axis_label="Temperature [degC]")
        depth_temperature.y_range = DataRange1d(flipped=True)
        depth_conductivity = self.get_fig_fct_depth(x_axis_label="Conductivity [S/m]")
        depth_salinity = self.get_fig_fct_depth(x_axis_label="Salinity [dimensionless]")
        pressure_oxygen = self.get_fig_fct_depth(x_axis_label="Oxygen [umol/L]")
        pressure_sigma = self.get_fig_fct_depth(x_axis_label="SigmaTheta [kg/m^3]")
        oxygen_sat = self.get_fig_fct_depth(x_axis_label="Oxygen saturation [%]")
        turbidity = self.get_fig_fct_depth(x_axis_label="Turbidity")
        for fi in [
            depth_conductivity,
            depth_salinity,
            pressure_oxygen,
            pressure_sigma,
            oxygen_sat,
            turbidity,
        ]:
            fi.y_range = depth_temperature.y_range

        self.scatter_fct_depth(
            fig=depth_temperature, x="temp", source=self.col_src_bin, color="green"
        )
        self.line_fct_depth(
            fig=depth_temperature, x="temp", source=self.col_src_bin, color="green"
        )

        self.depth_temperature = depth_temperature

        # Set up depth vs conductivity plot settings
        self.scatter_fct_depth(
            fig=depth_conductivity, x="cond", source=self.col_src_bin, color="green"
        )
        self.line_fct_depth(
            fig=depth_conductivity, x="cond", source=self.col_src_bin, color="green"
        )

        self.depth_conductivity = depth_conductivity

        # Set up depth vs salinity plot settings
        self.scatter_fct_depth(
            fig=depth_salinity, x="sal", source=self.col_src_bin, color="green"
        )
        self.line_fct_depth(
            fig=depth_salinity, x="sal", source=self.col_src_bin, color="green"
        )

        self.depth_salinity = depth_salinity

        # Set up pressure vs oxygen conc plot settings
        self.scatter_fct_depth(
            fig=pressure_oxygen, x="oxy_conc", source=self.col_src_bin, color="green"
        )
        self.line_fct_depth(
            fig=pressure_oxygen, x="oxy_conc", source=self.col_src_bin, color="green"
        )

        self.pressure_oxygen = pressure_oxygen

        # Set up pressure vs sigma-theta plot settings
        self.scatter_fct_depth(
            fig=pressure_sigma, x="sigma-theta", source=self.col_src_bin, color="green"
        )
        self.line_fct_depth(
            fig=pressure_sigma, x="sigma-theta", source=self.col_src_bin, color="green"
        )

        self.pressure_sigma = pressure_sigma

        self.scatter_fct_depth(
            fig=oxygen_sat, x="oxy_sat", source=self.col_src_bin, color="green"
        )
        self.line_fct_depth(
            fig=oxygen_sat, x="oxy_sat", source=self.col_src_bin, color="green"
        )

        self.oxygen_sat = oxygen_sat

        self.scatter_fct_depth(
            fig=turbidity, x="TurbidityMeter_0", source=self.col_src_bin, color="green"
        )
        self.line_fct_depth(
            fig=turbidity, x="TurbidityMeter_0", source=self.col_src_bin, color="green"
        )

        self.turbidity = turbidity

        # Set up T-S plot settings
        ts_plot = figure(
            x_axis_label="Salinity [dimensionless]",
            y_axis_label="Temperature [degC]",
            x_axis_location="below",
            tools="pan,wheel_zoom,box_zoom,box_select,tap,reset",
            toolbar_location="above",
            width=400,
            height=450,
            output_backend="webgl",
        )
        # Set linear colour mapping
        mapper = linear_cmap(
            field_name="oxy_conc",
            palette=Viridis256,
            low=self.col_src_ts.data["oxy_conc"].min(),  # type: ignore
            high=self.col_src_ts.data["oxy_conc"].max(),  # type: ignore
        )
        color_bar = ColorBar(
            color_mapper=mapper["transform"],
            width=30,
            location=(0, 0),
            title="umol/L",
        )
        ts_plot.add_layout(color_bar, "right")

        # Set annotated boxes for water mass descriptions from water_mass_configuration import patch_dict, box_dict
        for item in patch_dict.keys():
            ts_plot.patch(
                patch_dict[item]["patch_coords"][0],
                patch_dict[item]["patch_coords"][1],
                line_color="red",
                line_width=1,
                alpha=0.5,
                fill_color="red",
                fill_alpha=0.1,
            )
            ts_plot.add_layout(
                Label(
                    x=patch_dict[item]["label_coords"][0],
                    y=patch_dict[item]["label_coords"][1],
                    x_units="data",
                    y_units="data",
                    text=patch_dict[item]["label"],
                    text_align="center",
                    text_baseline="middle",
                )
            )

        for item in box_dict.keys():
            top = box_dict[item]["box_coords"]["top"]
            right = box_dict[item]["box_coords"]["right"]
            bottom = box_dict[item]["box_coords"]["bottom"]
            left = box_dict[item]["box_coords"]["left"]
            ts_plot.add_layout(
                BoxAnnotation(
                    top=top,
                    bottom=bottom,
                    left=left,
                    right=right,
                    line_color="red",
                    line_width=1,
                    line_alpha=0.5,
                    fill_color="red",
                    fill_alpha=0.1,
                )
            )
            ts_plot.add_layout(
                Label(
                    x=box_dict[item]["label_coords"][0],
                    y=box_dict[item]["label_coords"][1],
                    x_units="data",
                    y_units="data",
                    text=box_dict[item]["label"],
                    text_align="center",
                    text_baseline="middle",
                )
            )

        # Add data to plot
        ts_plot.scatter(
            "sal",
            "temp",
            source=self.col_src_ts,
            color=mapper,
            fill_alpha=0.2,
            size=5,
        )
        self.ts_plot = ts_plot

        # Set up plot figure for section
        temp_section = figure(
            tools="pan,wheel_zoom,box_zoom,box_select,tap,reset",
            x_axis_location="above",
            y_axis_label="Depth [m]",
            y_range=DataRange1d(flipped=True),
            output_backend="webgl",
        )
        # Set linear colour mapping for temperature
        temperature_color_mapper = linear_cmap(
            field_name="temp",
            palette=Viridis256,
            low=self.col_src_ts.data["temp"].min(),  # type: ignore
            high=self.col_src_ts.data["temp"].max(),  # type: ignore
        )
        temperature_color_bar = ColorBar(
            color_mapper=temperature_color_mapper["transform"],
            width=30,
            location=(0, 0),
            title="degrees C",
        )
        temp_section.add_layout(temperature_color_bar, "right")
        # Add data to plot
        temp_section.scatter(
            "SectionX",
            "depth",
            source=self.col_src_ts,
            color=temperature_color_mapper,
            fill_alpha=0.2,
            size=5,
        )
        self.temp_section = temp_section

        # Set up plot figure for salinity section
        sal_section = figure(
            tools="pan,wheel_zoom,box_zoom,box_select,tap,reset",
            x_axis_location="above",
            y_axis_label="Depth [m]",
            y_range=DataRange1d(flipped=True),
            output_backend="webgl",
        )
        # Set linear colour mapping for salinity
        salinity_color_mapper = linear_cmap(
            field_name="sal",
            palette=Viridis256,
            low=self.col_src_ts.data["sal"].min(),  # type: ignore
            high=self.col_src_ts.data["sal"].max(),  # type: ignore
        )
        salinity_color_bar = ColorBar(
            color_mapper=salinity_color_mapper["transform"],
            width=30,
            location=(0, 0),
            title="PSU",
        )
        sal_section.add_layout(salinity_color_bar, "right")
        # Add data to plot
        sal_section.scatter(
            "SectionX",
            "depth",
            source=self.col_src_ts,
            color=salinity_color_mapper,
            fill_alpha=0.2,
            size=5,
        )
        self.sal_section = sal_section

        # Set up plot figure for dissolved oxyen section
        doxy_section = figure(
            tools="pan,wheel_zoom,box_zoom,box_select,tap,reset",
            x_axis_location="above",
            y_axis_label="Depth [m]",
            y_range=DataRange1d(flipped=True),
            output_backend="webgl",
        )
        # Set linear colour mapping
        doxy_color_mapper = linear_cmap(
            field_name="oxy_conc",
            palette=Viridis256,
            low=self.col_src_ts.data["oxy_conc"].min(),  # type: ignore
            high=self.col_src_ts.data["oxy_conc"].max(),  # type: ignore
        )
        doxy_color_bar = ColorBar(
            color_mapper=doxy_color_mapper["transform"],
            width=30,
            location=(0, 0),
            title="umol/L",
        )
        doxy_section.add_layout(doxy_color_bar, "right")
        # Add data to plot
        doxy_section.scatter(
            "SectionX",
            "depth",
            source=self.col_src_ts,
            color=doxy_color_mapper,
            fill_alpha=0.2,
            size=5,
        )
        self.doxy_section = doxy_section

    # Add update functions
    def update_binning_plot(self, attr, old, new):
        # Update the ColumnDataSource for the profile plots
        df_st_updated = self.profile_data.loc[
            self.profile_data["CTD number"] == self.profile.value,
            list(self.get_suite_dict().values()),
        ].copy(deep=True)
        df_st_updated = df_st_updated.rename(
            columns={v: k for k, v in self.get_suite_dict().items()}
        )
        src_updated = ColumnDataSource(df_st_updated)
        self.col_src_bin.data.update(src_updated.data)

        self.update_button_avail()

        # Update ColumnDataSource for T-S plot
        df_ts_updated = self.profile_data.loc[
            :, list(self.get_suite_dict().values())
        ].copy(deep=True)
        df_ts_updated = df_ts_updated.rename(
            columns={v: k for k, v in self.get_suite_dict().items()}
        )
        df_ts_updated["SectionX"] = df_ts_updated[self.x_axis_filter.value]
        src_ts_updated = ColumnDataSource(df_ts_updated)
        self.col_src_ts.data.update(src_ts_updated.data)

    def bin_screen(self, doc):

        self.bin_data()

        # Link update functions to interactive widgets
        self.profile.on_change("value", self.update_binning_plot)
        self.x_axis_filter.on_change("value", self.update_binning_plot)
        self.next_profile.on_click(self.next_pf)
        self.prev_profile.on_click(self.prev_pf)
        self.sensor_suite.on_change("active", self.update_binning_plot)
        self.screen_print.on_click(self.screen_html)

        # Define dashboard layout
        layout = column(
            row(
                Spacer(width=40),
                self.prev_profile,
                Spacer(width=50),
                self.profile,
                self.next_profile,
                Spacer(width=150),
                self.sensor_suite,
                Spacer(width=50),
                self.screen_print,
            ),
            row(
                gridplot(
                    [
                        self.depth_temperature,
                        self.depth_conductivity,
                        self.depth_salinity,
                        self.pressure_oxygen,
                        self.pressure_sigma,
                    ],
                    ncols=5,
                    width=250,
                    height=450,
                ),
            ),
            row(
                Spacer(width=395),
                gridplot(
                    [self.oxygen_sat, self.turbidity],
                    ncols=2,
                    width=230,
                    height=450,
                ),
            ),
            row(Spacer(width=300), self.x_axis_filter),
            row(
                self.survey_map,
                gridplot(
                    [
                        self.temp_section,
                        self.sal_section,
                        self.doxy_section,
                    ],
                    ncols=1,
                    width=600,
                    height=200,
                ),
                self.ts_plot,
            ),
        )
        self.visualisation_layout = layout
        # Add layout to document
        doc.add_root(layout)

    def bin_data_overlay(self):
        self.screen_print = Button(
            label="Save as HTML",
            button_type="default",
            width=50,
            disabled=False,
        )
        self.sensor_suite = RadioGroup(
            labels=["primary", "secondary"],
            active=0,
        )
        self.x_axis_filter = Select(
            options=["Longitude [degrees_east]", "Latitude [degrees_north]", "Date"],
            value="Longitude [degrees_east]",
        )

        # Define the ColumnDataSource for the profile plots

        self.suite = list(self.get_suite_dict().values())

        # self.renamed = list(suite_dict.keys())

        df_st = self.profile_data[self.suite].copy(deep=True)
        df_st = df_st.rename(columns={v: k for k, v in self.get_suite_dict().items()})

        self.col_src_bin = ColumnDataSource(df_st)
        self.col_src_metadata = ColumnDataSource(
            self.profile_data[["CTD number", "Eastings", "Northings"]].drop_duplicates()
        )

        # Define ColumnDataSource for T-S plot
        df_ts = self.profile_data[self.suite].copy(deep=True)
        df_ts = df_ts.rename(columns={v: k for k, v in self.get_suite_dict().items()})
        df_ts["SectionX"] = df_ts[self.x_axis_filter.value]
        self.col_src_ts = ColumnDataSource(df_ts)

        # Map plot
        survey_map = figure(
            tools="pan,wheel_zoom,box_zoom,box_select,tap,reset",
            x_axis_type="mercator",
            y_axis_type="mercator",
            width=300,
            height=300,
            toolbar_location="above",
            output_backend="webgl",
        )
        survey_map.add_tile("CartoDB Positron", retina=True)
        survey_map.xaxis.axis_label = "Longitude [degrees E]"
        survey_map.yaxis.axis_label = "Latitude [degrees N]"

        survey_map.scatter(
            x="Eastings",
            y="Northings",
            size=5,
            fill_color="blue",
            fill_alpha=0.5,
            source=self.col_src_ts,
        )

        survey_map.scatter(
            x="Eastings",
            y="Northings",
            size=5,
            fill_color="red",
            fill_alpha=1.0,
            selection_fill_color="red",
            source=self.col_src_bin,
        )

        self.survey_map = survey_map

        # Set up depth vs quantity plots
        depth_temperature = self.get_fig_fct_depth(x_axis_label="Temperature [degC]")
        depth_temperature.y_range = DataRange1d(flipped=True)

        depth_conductivity = self.get_fig_fct_depth(x_axis_label="Conductivity [S/m]")
        depth_salinity = self.get_fig_fct_depth(x_axis_label="Salinity [dimensionless]")

        pressure_oxygen = self.get_fig_fct_depth(x_axis_label="Oxygen [umol/L]")
        pressure_sigma = self.get_fig_fct_depth(x_axis_label="SigmaTheta [kg/m^3]")
        oxygen_sat = self.get_fig_fct_depth(x_axis_label="Oxygen saturation [%]")
        turbidity = self.get_fig_fct_depth(x_axis_label="Turbidity")

        # Add data to plot
        palette = cycle(Category10[10])
        renderer_list = []
        color_list = []
        label_list = []
        for i, cast_i in enumerate(self.profile_data["CTD number"].unique()):
            label_list += [cast_i]
            color_i = next(palette)
            color_list += [color_i]
            data_i = self.profile_data.loc[
                self.profile_data["CTD number"] == cast_i, self.suite
            ]
            data_i = data_i.rename(
                columns={v: k for k, v in self.get_suite_dict().items()}
            )
            source_i = ColumnDataSource(data_i)
            self.scatter_fct_depth(
                fig=depth_temperature, x="temp", source=source_i, color=color_i
            )
            li = self.line_fct_depth(
                fig=depth_temperature, x="temp", source=source_i, color=color_i
            )

            renderer_list += [li]
            # Add data to figures
            self.scatter_fct_depth(
                fig=depth_salinity, x="sal", source=source_i, color=color_i
            )
            self.line_fct_depth(
                fig=depth_salinity, x="sal", source=source_i, color=color_i
            )

            self.scatter_fct_depth(
                fig=pressure_oxygen, x="oxy_conc", source=source_i, color=color_i
            )
            self.line_fct_depth(
                fig=pressure_oxygen, x="oxy_conc", source=source_i, color=color_i
            )

            self.scatter_fct_depth(
                fig=depth_conductivity, x="cond", source=source_i, color=color_i
            )
            self.line_fct_depth(
                fig=depth_conductivity, x="cond", source=source_i, color=color_i
            )

            self.scatter_fct_depth(
                fig=pressure_sigma, x="sigma-theta", source=source_i, color=color_i
            )
            self.line_fct_depth(
                fig=pressure_sigma, x="sigma-theta", source=source_i, color=color_i
            )

            self.scatter_fct_depth(
                fig=oxygen_sat, x="oxy_sat", source=source_i, color=color_i
            )
            self.line_fct_depth(
                fig=oxygen_sat, x="oxy_sat", source=source_i, color=color_i
            )

            self.scatter_fct_depth(
                fig=turbidity, x="TurbidityMeter_0", source=source_i, color=color_i
            )
            self.line_fct_depth(
                fig=turbidity, x="TurbidityMeter_0", source=source_i, color=color_i
            )

        legend_items = [
            LegendItem(
                label=label_list[i],
                renderers=[
                    renderer
                    for renderer in renderer_list
                    if renderer.glyph.line_color == color
                ],
            )
            for i, color in enumerate(color_list)
        ]

        ## Use a dummy figure for the LEGEND
        dum_fig = figure(
            width=1000,
            height=50,
            outline_line_alpha=0,
            toolbar_location=None,
        )
        # set the components of the figure invisible
        for fig_component in [
            dum_fig.grid[0],
            dum_fig.ygrid[0],
            dum_fig.xaxis[0],
            dum_fig.yaxis[0],
        ]:
            fig_component.visible = False
        # The glyphs referred by the legend need to be present in the figure that holds the legend, so we must add them to the figure renderers
        dum_fig.renderers += renderer_list  # type: ignore
        # set the figure range outside of the range of all glyphs
        dum_fig.x_range.end = 1005
        dum_fig.x_range.start = 1000
        # add the legend
        dum_fig.add_layout(
            Legend(
                orientation="horizontal",
                click_policy="hide",
                location="top_left",
                border_line_alpha=0,
                items=legend_items,
            )
        )
        self.legend_fig = dum_fig

        for fi in [
            depth_conductivity,
            depth_salinity,
            pressure_oxygen,
            pressure_sigma,
            oxygen_sat,
            turbidity,
        ]:
            fi.y_range = depth_temperature.y_range

        self.depth_temperature = depth_temperature
        self.depth_conductivity = depth_conductivity
        self.depth_salinity = depth_salinity
        self.pressure_oxygen = pressure_oxygen
        self.pressure_sigma = pressure_sigma
        self.oxygen_sat = oxygen_sat
        self.turbidity = turbidity

        # Set up T-S plot settings
        ts_plot = figure(
            x_axis_label="Salinity [dimensionless]",
            y_axis_label="Temperature [degC]",
            x_axis_location="below",
            tools="pan,wheel_zoom,box_zoom,box_select,tap,reset",
            toolbar_location="above",
            width=400,
            height=450,
            output_backend="webgl",
        )
        # Set linear colour mapping
        mapper = linear_cmap(
            field_name="oxy_conc",
            palette=Viridis256,
            low=self.col_src_ts.data["oxy_conc"].min(),  # type: ignore
            high=self.col_src_ts.data["oxy_conc"].max(),  # type: ignore
        )
        color_bar = ColorBar(
            color_mapper=mapper["transform"],
            width=30,
            location=(0, 0),
            title="umol/L",
        )
        ts_plot.add_layout(color_bar, "right")

        # Set annotated boxes for water mass descriptions from water_mass_configuration import patch_dict, box_dict
        for item in patch_dict.keys():
            ts_plot.patch(
                patch_dict[item]["patch_coords"][0],
                patch_dict[item]["patch_coords"][1],
                line_color="red",
                line_width=1,
                alpha=0.5,
                fill_color="red",
                fill_alpha=0.1,
            )
            ts_plot.add_layout(
                Label(
                    x=patch_dict[item]["label_coords"][0],
                    y=patch_dict[item]["label_coords"][1],
                    x_units="data",
                    y_units="data",
                    text=patch_dict[item]["label"],
                    text_align="center",
                    text_baseline="middle",
                )
            )

        for item in box_dict.keys():
            top = box_dict[item]["box_coords"]["top"]
            right = box_dict[item]["box_coords"]["right"]
            bottom = box_dict[item]["box_coords"]["bottom"]
            left = box_dict[item]["box_coords"]["left"]
            ts_plot.add_layout(
                BoxAnnotation(
                    top=top,
                    bottom=bottom,
                    left=left,
                    right=right,
                    line_color="red",
                    line_width=1,
                    line_alpha=0.5,
                    fill_color="red",
                    fill_alpha=0.1,
                )
            )
            ts_plot.add_layout(
                Label(
                    x=box_dict[item]["label_coords"][0],
                    y=box_dict[item]["label_coords"][1],
                    x_units="data",
                    y_units="data",
                    text=box_dict[item]["label"],
                    text_align="center",
                    text_baseline="middle",
                )
            )

        # Add data to plot
        ts_plot.scatter(
            "sal",
            "temp",
            source=self.col_src_ts,
            color=mapper,
            fill_alpha=0.2,
            size=5,
        )
        self.ts_plot = ts_plot

        # Set up plot figure for section
        temp_section = figure(
            tools="pan,wheel_zoom,box_zoom,box_select,tap,reset",
            x_axis_location="above",
            y_axis_label="Depth [m]",
            y_range=DataRange1d(flipped=True),
            output_backend="webgl",
        )
        # Set linear colour mapping for temperature
        temperature_color_mapper = linear_cmap(
            field_name="temp",
            palette=Viridis256,
            low=self.col_src_ts.data["temp"].min(),  # type: ignore
            high=self.col_src_ts.data["temp"].max(),  # type: ignore
        )
        temperature_color_bar = ColorBar(
            color_mapper=temperature_color_mapper["transform"],
            width=30,
            location=(0, 0),
            title="degrees C",
        )
        temp_section.add_layout(temperature_color_bar, "right")
        # Add data to plot
        temp_section.scatter(
            "SectionX",
            "depth",
            source=self.col_src_ts,
            color=temperature_color_mapper,
            fill_alpha=0.2,
            size=5,
        )
        self.temp_section = temp_section

        # Set up plot figure for salinity section
        sal_section = figure(
            tools="pan,wheel_zoom,box_zoom,box_select,tap,reset",
            x_axis_location="above",
            y_axis_label="Depth [m]",
            y_range=DataRange1d(flipped=True),
            output_backend="webgl",
        )
        # Set linear colour mapping for salinity
        salinity_color_mapper = linear_cmap(
            field_name="sal",
            palette=Viridis256,
            low=self.col_src_ts.data["sal"].min(),  # type: ignore
            high=self.col_src_ts.data["sal"].max(),  # type: ignore
        )
        salinity_color_bar = ColorBar(
            color_mapper=salinity_color_mapper["transform"],
            width=30,
            location=(0, 0),
            title="PSU",
        )
        sal_section.add_layout(salinity_color_bar, "right")
        # Add data to plot
        sal_section.scatter(
            "SectionX",
            "depth",
            source=self.col_src_ts,
            color=salinity_color_mapper,
            fill_alpha=0.2,
            size=5,
        )
        self.sal_section = sal_section

        # Set up plot figure for dissolved oxyen section
        doxy_section = figure(
            tools="pan,wheel_zoom,box_zoom,box_select,tap,reset",
            x_axis_location="above",
            y_axis_label="Depth [m]",
            y_range=DataRange1d(flipped=True),
            output_backend="webgl",
        )
        # Set linear colour mapping
        doxy_color_mapper = linear_cmap(
            field_name="oxy_conc",
            palette=Viridis256,
            low=self.col_src_ts.data["oxy_conc"].min(),  # type: ignore
            high=self.col_src_ts.data["oxy_conc"].max(),  # type: ignore
        )
        doxy_color_bar = ColorBar(
            color_mapper=doxy_color_mapper["transform"],
            width=30,
            location=(0, 0),
            title="umol/L",
        )
        doxy_section.add_layout(doxy_color_bar, "right")
        # Add data to plot
        doxy_section.scatter(
            "SectionX",
            "depth",
            source=self.col_src_ts,
            color=doxy_color_mapper,
            fill_alpha=0.2,
            size=5,
        )
        self.doxy_section = doxy_section

    def bin_screen_overlay(self, doc):

        self.bin_data_overlay()

        # Define dashboard layout
        layout = column(
            row(
                Spacer(width=40 + 50 + 150 + 50 + 150),
                self.sensor_suite,
                Spacer(width=50),
                self.screen_print,
            ),
            row(self.legend_fig),
            row(
                gridplot(
                    [
                        self.depth_temperature,
                        self.depth_conductivity,
                        self.depth_salinity,
                        self.pressure_oxygen,
                        self.pressure_sigma,
                    ],
                    ncols=5,
                    width=250,
                    height=450,
                ),
            ),
            row(
                Spacer(width=395),
                gridplot(
                    [self.oxygen_sat, self.turbidity],
                    ncols=2,
                    width=230,
                    height=450,
                ),
            ),
        )
        self.visualisation_layout = layout
        # Add layout to document
        doc.add_root(layout)
