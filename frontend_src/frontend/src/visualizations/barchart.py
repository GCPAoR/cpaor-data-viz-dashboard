from typing import Tuple

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from frontend.src.utils.utils_functions import _add_source
from matplotlib.colors import LinearSegmentedColormap


def _get_abbreviated_number(number: int) -> str:
    """
    Abbreviate a number to a more readable format.
    """
    if number < 1000:
        return str(number)
    elif number < 1000000:
        return str(int(number / 1_000)) + " k"
    else:
        return str(round(number / 1_000_000, 1)) + " million"


@st.fragment
def _display_stackbar(displayed_values: dict):
    """
    Creates and displays a horizontal stacked bar chart.

    Parameters:
    displayed_values (dict): Contains data for plotting the stacked bar chart.
        - 'original_numbers' (list of dicts): Each dict contains:
            - 'value' (int/float): Value for the segment.
            - 'label' (str): Label for the segment.
            - 'color' (str): Color for the segment.
            - 'number_annotation' (str): Annotation for the segment.
        - 'plot_size' (tuple): Size of the plot.
        - 'annotation' (str): Text to be displayed below the chart.

    Returns:
    None
    """

    n_segments = len(displayed_values["original_numbers"])

    tick_values = [
        displayed_values["original_numbers"][i]["value"] for i in range(n_segments)
    ]
    labels = [
        displayed_values["original_numbers"][i]["label"] for i in range(n_segments)
    ]
    colors = [
        displayed_values["original_numbers"][i]["color"] for i in range(n_segments)
    ]
    tick_labels = [
        displayed_values["original_numbers"][i]["number_annotation"]
        for i in range(n_segments)
    ]

    # Bar segments
    segments = [displayed_values["original_numbers"][0]["value"]] + [
        displayed_values["original_numbers"][i]["value"]
        - displayed_values["original_numbers"][i - 1]["value"]
        for i in range(1, n_segments)
    ]

    # Create the figure and axis
    fig, ax = plt.subplots(figsize=displayed_values["plot_size"])

    for i in range(n_segments):
        ax.barh(
            [0],
            [segments[i]],
            left=sum(segments[:i]),
            color=colors[i],
            edgecolor=colors[i],
        )

        if i == 0:
            displayed_text_placement = segments[i] / 2
        else:
            displayed_text_placement = sum(segments[:i]) + segments[i] / 2

        ax.text(
            displayed_text_placement,
            0,
            labels[i] if i != 1 else "",
            ha="center",
            va="center",
            color="black",
            fontsize=10,
        )

    # Make the axes invisible
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"]  # .set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.get_yaxis().set_ticks([])

    # Add x-axis ticks for each box delimitation and the 100% value
    # tick_labels = [f"{int(p)}%" for p in percentages] + ["100%"]
    ax.set_xticks(tick_values)
    ax.set_xticklabels(tick_labels, fontsize=10)

    # Remove y-axis and set limits
    ax.get_yaxis().set_visible(False)
    ax.set_xlim(0, tick_values[-1])

    # Add annotation for the percentage of children in need
    ax.annotate(
        f"\n\n{displayed_values['annotation']}",
        xy=(tick_values[-1] / 2, -0.2),
        xytext=(tick_values[-1] / 2, -0.5),
        ha="center",
        va="center",
        color="black",
        fontsize=10,
    )

    # Add a horizontal line above the bars indicating the value of the second bar
    if n_segments > 2:
        y_position = 0.45
        ax.plot(
            [0, tick_values[-2]],
            [y_position, y_position],
            color=colors[1],
            linestyle="-",
            linewidth=3,
        )
        ax.text(
            tick_values[-2] / 2,
            y_position + 0.05,  # Adjust y position as needed
            labels[1],
            ha="center",
            va="bottom",
            color="black",
            fontsize=10,
            # fontweight='bold',
        )

    # Set title
    st.pyplot(fig)


def create_continuous_cmap(colors, name="custom_cmap"):
    """Create a custom colormap using LinearSegmentedColormap."""
    cmap = LinearSegmentedColormap.from_list(name, colors, N=256)
    return cmap


@st.fragment
def _create_vertical_barplot(
    df: pd.DataFrame,
    labels_col: str,
    numbers_col: str,
    text_col: str,
    max_val: float = None,
    title: str = None,
    x_ax_title: str = None,
    y_ax_title: str = None,
    color="#D2E5B7",
):
    """
    Creates and displays a vertical bar plot.

    Parameters:
    df (pd.DataFrame): DataFrame containing the data.
    labels_col (str): Column name for the bar labels.
    numbers_col (str): Column name for the bar values.
    text_col (str): Column name for the text annotations.
    max_val (float, optional): Maximum value for the y-axis. Defaults to None.
    title (str, optional): Title of the plot. Defaults to None.
    x_ax_title (str, optional): Title of the x-axis. Defaults to None.
    y_ax_title (str, optional): Title of the y-axis. Defaults to None.
    color (str, optional): Color of the bars. Defaults to "#D2E5B7".

    Returns:
    None
    """

    scores = df[numbers_col].values
    labels = df[labels_col].values
    texts = df[text_col].values

    # Create the figure and axes
    fig, ax = plt.subplots(figsize=(10, 3.5))

    # Customize the axes
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=16, rotation=0)
    ax.set_yticks([])
    ax.set_xlim(-0.5, len(labels) - 0.5)
    ax.set_ylim(0, 1.05 * max(scores))

    ax.spines["top"].set_edgecolor("white")
    ax.spines["right"].set_edgecolor("white")
    # ax.spines['bottom'].set_edgecolor('white')
    ax.spines["left"].set_edgecolor("white")

    for i in range(len(scores)):
        ax.bar(i, scores[i], color=color, edgecolor="white", linewidth=1.2)

        ax.text(
            i,
            scores[i] + 0.1,
            f"{texts[i]}",
            ha="center",
            va="bottom",
            fontsize=14,
        )

    _add_plot_legend(ax, title=title, x_ax_title=x_ax_title, y_ax_title=y_ax_title)

    st.pyplot(fig)


def _customize_axes_horizontal_plot(ax, labels, max_val):
    # Customize the axes
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=16)

    ax.set_ylim(-0.5, len(labels) - 0.5)
    ax.set_xlim(0, max_val)

    ax.spines["top"].set_edgecolor("white")
    ax.spines["right"].set_edgecolor("white")
    ax.spines["left"].set_edgecolor("white")

    # if show_xscale:
    # ax.set_xticks([0, max_val])
    # ax.set_xticklabels([0, _get_abbreviated_number(max_val)], fontsize=16)
    # else:
    ax.set_xticks([])
    ax.spines["bottom"].set_edgecolor("white")


def _add_scores_text_horizontal_plot(ax, scores, shown_score_values):
    for i in range(len(shown_score_values)):
        ax.text(
            scores[i] * 1.05,
            i,
            f"{shown_score_values[i]}",
            ha="left",
            va="center",
            fontsize=14,
        )


def _add_plot_legend(
    ax, title: str = None, x_ax_title: str = None, y_ax_title: str = None
):
    # make the title bold
    if title:
        ax.set_title(title, fontsize=20)
    if x_ax_title:
        ax.set_xlabel(x_ax_title, fontsize=16)
    if y_ax_title:
        ax.set_ylabel(y_ax_title, fontsize=16)


# @st.fragment
# def _create_horizontal_single_scale_barplot(
#     df: pd.DataFrame,
#     labels_col: str,
#     numbers_col: str,
#     text_col: str,
#     max_val: int,
#     figsize: Tuple[int] = (10, 5),
#     color="#D2E5B7",
#     title: str = None,
#     x_ax_title: str = None,
#     y_ax_title: str = None,
# ):
#     """
#     Creates and displays a horizontal single scale bar plot.

#     Parameters:
#     df (pd.DataFrame): DataFrame containing the data.
#     labels_col (str): Column name for the bar labels.
#     numbers_col (str): Column name for the bar values.
#     text_col (str): Column name for the text annotations.
#     max_val (int): Maximum value for the x-axis.
#     figsize (Tuple[int], optional): Size of the plot. Defaults to (10, 5).
#     color (str, optional): Color of the bars. Defaults to "#D2E5B7".
#     title (str, optional): Title of the plot. Defaults to None.
#     x_ax_title (str, optional): Title of the x-axis. Defaults to None.
#     y_ax_title (str, optional): Title of the y-axis. Defaults to None.

#     Returns:
#     None
#     """

#     scores = df[numbers_col].values
#     labels = df[labels_col].values
#     shown_score_values = df[text_col].values

#     # Create the figure and axes
#     fig, ax = plt.subplots(figsize=figsize)

#     # Create the bars
#     for i, (label, score) in enumerate(zip(labels, scores)):
#         ax.barh(i, score, color=color, edgecolor="white", linewidth=1.2, height=0.4)

#     _customize_axes_horizontal_plot(ax, labels, max_val)

#     # Add the scores as text
#     _add_scores_text_horizontal_plot(ax, scores, shown_score_values)

#     _add_plot_legend(ax, title, x_ax_title, y_ax_title)

#     st.pyplot(fig, bbox_inches="tight", pad_inches=0.1)


@st.fragment
def _create_horizontal_continous_scale_barplot(
    df: pd.DataFrame,
    labels_col: str,
    numbers_col: str,
    text_col: str,
    max_val: int,
    color1="#D2E5B7",
    color2="#86789C",
    title: str = None,
    x_ax_title: str = None,
    y_ax_title: str = None,
    figsize: Tuple[int] = (10, 5),
):
    """
    Creates and displays a horizontal continuous scale bar plot.

    Parameters:
    df (pd.DataFrame): DataFrame containing the data.
    labels_col (str): Column name for the bar labels.
    numbers_col (str): Column name for the bar values.
    text_col (str): Column name for the text annotations.
    max_val (int): Maximum value for the x-axis.
    color1 (str, optional): Starting color of the gradient. Defaults to "#D2E5B7".
    color2 (str, optional): Ending color of the gradient. Defaults to "#86789C".
    title (str, optional): Title of the plot. Defaults to None.
    x_ax_title (str, optional): Title of the x-axis. Defaults to None.
    y_ax_title (str, optional): Title of the y-axis. Defaults to None.

    Returns:
    None
    """
    custom_cmap = create_continuous_cmap([color1, color2])

    norm = plt.Normalize(0, max_val)
    sm = plt.cm.ScalarMappable(cmap=custom_cmap, norm=norm)
    sm.set_array([])

    scores = df[numbers_col].values
    labels = df[labels_col].values
    shown_score_values = df[text_col].values

    # Create the figure and axes
    fig, ax = plt.subplots(figsize=figsize)

    # Create the bars
    for i, (label, score) in enumerate(zip(labels, scores)):
        color = custom_cmap(norm(score))
        ax.barh(i, score, color=color, edgecolor="white", linewidth=1.2, height=0.4)

    _customize_axes_horizontal_plot(ax, labels, max_val)

    # # Add colorbar
    # cbar = plt.colorbar(sm, ax=ax, orientation="horizontal", fraction=0.1, pad=0.04)
    # # cbar.set_label("Value", fontsize=10)
    # cbar.outline.set_edgecolor("white")

    # Add the scores as text
    _add_scores_text_horizontal_plot(ax, scores, shown_score_values)

    _add_plot_legend(ax, title, x_ax_title, y_ax_title)

    st.pyplot(fig, bbox_inches="tight", pad_inches=0.1)

    max_val = int(max_val)
    if max_val == 5:
        min_val = "0 (less severe)"
        max_val = "5 (more severe)"
    elif max_val == 100:
        min_val = "0%"
        max_val = "100%"
    else:
        min_val = "0"
        max_val = _get_abbreviated_number(max_val)

    _add_source(f"Scale: {min_val} to {max_val}", 0)
