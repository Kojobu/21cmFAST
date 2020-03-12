"""Simple plotting functions for 21cmFAST objects."""

from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors

from . import outputs
from .outputs import Coeval
from .outputs import LightCone

eor_colour = colors.LinearSegmentedColormap.from_list(
    "EoR",
    [
        (0, "white"),
        (0.21, "yellow"),
        (0.42, "orange"),
        (0.63, "red"),
        (0.86, "black"),
        (0.9, "blue"),
        (1, "cyan"),
    ],
)
plt.register_cmap(cmap=eor_colour)


def _imshow_slice(
    cube,
    slice_axis=-1,
    slice_index=0,
    fig=None,
    ax=None,
    fig_kw=None,
    cbar=True,
    cbar_horizontal=False,
    rotate=False,
    cmap="EoR",
    **imshow_kw,
):
    """
    Plot a slice of some kind of cube.

    Parameters
    ----------
    cube : nd-array
        A 3D array of some quantity.
    slice_axis : int, optional
        The axis over which to take a slice, in order to plot.
    slice_index :
        The index of the slice.
    fig : Figure object
        An optional matplotlib figure object on which to plot
    ax : Axis object
        The matplotlib axis object on which to plot (created by default).
    fig_kw :
        Optional arguments passed to the figure construction.
    cbar : bool
        Whether to plot the colorbar
    cbar_horizontal : bool
        Whether the colorbar should be horizontal underneath the plot.
    rotate : bool
        Whether to rotate the plot vertically.
    imshow_kw :
        Optional keywords to pass to :func:`maplotlib.imshow`.

    Returns
    -------
    fig, ax :
        The figure and axis objects from matplotlib.
    """
    # If no axis is passed, create a new one
    # This allows the user to add this plot into an existing grid, or alter it afterwards.
    if fig_kw is None:
        fig_kw = {}
    if ax is None and fig is None:
        fig, ax = plt.subplots(1, 1, **fig_kw)
    elif ax is None:
        ax = plt.gca()
    elif fig is None:
        fig = plt.gcf()

    plt.sca(ax)

    if slice_index >= cube.shape[slice_axis]:
        raise IndexError(
            "slice_index is too large for that axis (slice_index=%s >= %s"
            % (slice_index, cube.shape[slice_axis])
        )

    slc = np.take(cube, slice_index, axis=slice_axis)
    if not rotate:
        slc = slc.T

    if cmap == "EoR":
        imshow_kw["vmin"] = -150
        imshow_kw["vmax"] = 30

    plt.imshow(slc, origin="lower", cmap=cmap, **imshow_kw)

    if cbar:
        cb = plt.colorbar(
            orientation="horizontal" if cbar_horizontal else "vertical", aspect=40
        )
        cb.outline.set_edgecolor(None)

    return fig, ax


def coeval_sliceplot(
    struct: [outputs._OutputStruct, Coeval],
    kind: [str, None] = None,
    cbar_label: [str, None] = None,
    **kwargs,
):
    """
    Show a slice of a given coeval box.

    Parameters
    ----------
    struct : :class:`~outputs._OutputStruct` or :class:`~wrapper.Coeval` instance
        The output of a function such as `ionize_box` (a class containing several quantities), or
        `run_coeval`.
    kind : str
        The quantity within the structure to be shown.
    cbar_label : str, optional
        A label for the colorbar. Some values of `kind` will have automatically chosen
        labels, but these can be turned off by setting ``cbar_label=''``.

    Returns
    -------
    fig, ax :
        figure and axis objects from matplotlib

    Other Parameters
    ----------------
    All other parameters are passed directly to :func:`_imshow_slice`. These include `slice_axis`
    and `slice_index`,
    which choose the actual slice to plot, optional `fig` and `ax` keywords which enable
    over-plotting previous figures,
    and the `imshow_kw` argument, which allows arbitrary styling of the plot.
    """
    if kind is None and isinstance(struct, outputs._OutputStruct):
        kind = struct.fieldnames[0]
    elif kind is None and isinstance(struct, Coeval):
        kind = "brightness_temp"

    try:
        cube = getattr(struct, kind)
    except AttributeError:
        raise AttributeError(
            "The given OutputStruct does not have the quantity {kind}".format(kind=kind)
        )

    if kind != "brightness_temp" and "cmap" not in kwargs:
        kwargs["cmap"] = "viridis"

    fig, ax = _imshow_slice(cube, extent=(0, struct.user_params.BOX_LEN) * 2, **kwargs)

    slice_axis = kwargs.get("slice_axis", -1)

    # Determine which axes are being plotted.
    if slice_axis in (2, -1):
        xax = "x"
        yax = "y"
    elif slice_axis == 1:
        xax = "x"
        yax = "z"
    elif slice_axis == 0:
        xax = "y"
        yax = "z"
    else:
        raise ValueError("slice_axis should be between -1 and 2")

    # Now put on the decorations.
    ax.set_xlabel("{xax}-axis [Mpc]".format(xax=xax))
    ax.set_ylabel("{yax}-axis [Mpc]".format(yax=yax))

    cbar = fig._gci().colorbar

    if cbar_label is None:
        if kind == "brightness_temp":
            cbar_label = r"Brightness Temperature, $\delta T_B$ [mK]"
        elif kind == "xH_box":
            cbar_label = r"Ionized fraction"

    cbar.ax.set_ylabel(cbar_label)

    return fig, ax


def lightcone_sliceplot(
    lightcone: LightCone,
    kind: str = "brightness_temp",
    lightcone2: LightCone = None,
    vertical: bool = False,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    cbar_label=None,
    **kwargs,
):
    """Create a 2D plot of a slice through a lightcone.

    Parameters
    ----------
    lightcone : :class:`~py21cmfast.wrapper.Lightcone`
        The lightcone object to plot
    kind : str, optional
        The attribute of the lightcone to plot. Must be an array.
    lightcone2 : str, optional
        If provided, plot the _difference_ of the selected attribute between the two
        lightcones.
    vertical : bool, optional
        Whether to plot the redshift in the vertical direction.
    cbar_label : str, optional
        A label for the colorbar. Some quantities have automatically chosen labels, but
        these can be removed by setting `cbar_label=''`.
    kwargs :
        Passed through to ``imshow()``.

    Returns
    -------
    fig :
        The matplotlib Figure object
    ax :
        The matplotlib Axis object onto which the plot was drawn.
    """
    slice_axis = kwargs.pop("slice_axis", 0)

    if slice_axis == 0:
        if xlabel is None:
            xlabel = "Redshift Axis [Mpc]"
        if ylabel is None:
            ylabel = "y-axis [Mpc]"

        if vertical:
            extent = (
                0,
                lightcone.user_params.BOX_LEN,
                0,
                lightcone.lightcone_coords[-1],
            )
            xlabel, ylabel = ylabel, xlabel
        else:
            extent = (
                0,
                lightcone.lightcone_coords[-1],
                0,
                lightcone.user_params.BOX_LEN,
            )

    else:
        extent = (0, lightcone.user_params.BOX_LEN) * 2

        if slice_axis == 1:
            if xlabel is None:
                xlabel = "x-axis [Mpc]"
            if ylabel is None:
                ylabel = "Redshift Axis [Mpc]"

        elif slice_axis in (2, -1):
            xlabel = "x-axis [Mpc]" if xlabel is None else xlabel
            ylabel = "y-axis [Mpc]" if ylabel is None else ylabel
        else:
            raise ValueError("slice_axis must be between -1 and 2")

    if lightcone2 is None:
        fig, ax = _imshow_slice(
            getattr(lightcone, kind),
            extent=extent,
            slice_axis=slice_axis,
            rotate=not vertical,
            cbar_horizontal=not vertical,
            cmap=kwargs.get("cmap", "EoR" if kind == "brightness_temp" else "viridis"),
            **kwargs,
        )
    else:
        d = getattr(lightcone, kind) - getattr(lightcone2, kind)
        fig, ax = _imshow_slice(
            d,
            extent=extent,
            slice_axis=slice_axis,
            rotate=not vertical,
            cbar_horizontal=not vertical,
            cmap=kwargs.pop("cmap", "bwr"),
            vmin=-np.abs(d.max()),
            vmax=np.abs(d.max()),
            **kwargs,
        )

    if ylabel:
        ax.set_ylabel(ylabel)
    if xlabel:
        ax.set_xlabel(xlabel)

    # Get redshift ticks.
    lc_z = lightcone.lightcone_redshifts
    zticks = np.arange(int(np.ceil(lc_z.min())), int(lc_z.max()) + 1)
    n_sep = len(zticks) // 8 + 1
    zticks = zticks[::n_sep]

    d_ticks = (
        lightcone.cosmo_params.cosmo.comoving_distance(zticks).value
        - lightcone.lightcone_distances[0]
    )
    if vertical:
        ax.set_yticks(d_ticks)
        ax.set_yticklabels(zticks)
    else:
        ax.set_xticks(d_ticks)
        ax.set_xticklabels(zticks)

    cbar = fig._gci().colorbar

    if cbar_label is None:
        if kind == "brightness_temp":
            cbar_label = r"Brightness Temperature, $\delta T_B$ [mK]"
        elif kind == "xH":
            cbar_label = r"Neutral fraction"

    if vertical:
        cbar.ax.set_ylabel(cbar_label)
    else:
        cbar.ax.set_xlabel(cbar_label)

    return fig, ax


def lightcone_sliceplot_all(
    lightcone: LightCone, vertical: bool = False, **kwargs,
):
    """
    Make a lightcone sliceplot for all quantities in a lightcone, side-by-side.

    Parameters
    ----------
    lightcone : :class:`LightCone` instance.
        The lightcone to plot.
    vertical : bool, optional
        Whether the redshift axis should run vertically in the plot.
    kwargs :
        Passed on to :func:`_imshow_slice` (and in turn `imshow`).


    Returns
    -------
    fig, ax :
        The matplotlib Figure and Axes on which the plot was made.
    """
    quantities = lightcone.quantities.keys()

    cmaps = {
        "brightness_temp": eor_colour,
        "Ts_box": "Reds",
        "xH_box": "magma",
        "dNrec_box": "magma",
        "z_re_box": "magma",
        "Gamma12_box": "cubehelix",
        "density": "viridis",
    }

    if vertical:
        fig, ax = plt.subplots(
            1,
            len(quantities),
            figsize=(
                lightcone.shape[1] * 0.015 * len(quantities),
                lightcone.shape[2] * 0.015,
            ),
            gridspec_kw={"wspace": 0.01},
            sharex=True,
            sharey=True,
        )
    else:
        fig, ax = plt.subplots(
            len(quantities),
            1,
            figsize=(
                lightcone.shape[2] * 0.015,
                lightcone.shape[1] * 0.015 * len(quantities),
            ),
            gridspec_kw={"hspace": 0.01},
            sharex=True,
            sharey=True,
        )

    for i, quantity in enumerate(quantities):
        lightcone_sliceplot(
            lightcone,
            kind=quantity,
            vertical=vertical,
            fig=fig,
            ax=ax[i],
            xlabel=None if i == (len(quantities) - 1) and vertical else "",
            ylabel=None if i == 0 and vertical else "",
            cmap=cmaps.get(quantity, None),
            cbar=False,
            **kwargs,
        )

        ax[i].text(
            1,
            0.05,
            quantity,
            horizontalalignment="right",
            verticalalignment="bottom",
            transform=ax[i].transAxes,
            color="red",
            backgroundcolor="white",
            fontsize=15,
        )

    plt.tight_layout()


def plot_global_history(
    lightcone: [LightCone],
    kind: [str, None] = None,
    ylabel: [str, None] = None,
    ax: [plt.Axes, None] = None,
):
    """
    Plot the global history of a given quantity from a lightcone.

    Parameters
    ----------
    lightcone : :class:`~LightCone` instance
        The lightcone containing the quantity to plot.
    kind : str, optional
        The quantity to plot. Must be in the `global_quantities` dict in the lightcone.
        By default, will choose the first entry in the dict.
    ylabel : str, optional
        A y-label for the plot. If None, will use ``kind``.
    ax : Axes, optional
        The matplotlib Axes object on which to plot. Otherwise, created.
    """
    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=(4, 7))
    else:
        fig = ax._gci().figure

    if kind is None:
        kind = list(lightcone.global_quantities.keys())[0]

    assert (
        kind in lightcone.global_quantities
        or hasattr(lightcone, "global_" + kind)
        or (kind.startswith("global_") and hasattr(lightcone, kind))
    )

    if kind in lightcone.global_quantities:
        value = lightcone.global_quantities[kind]
    elif kind.startswith("global)"):
        value = getattr(lightcone, kind)
    else:
        value = getattr(lightcone, "global_" + kind)

    ax.plot(lightcone.node_redshifts, value)
    ax.set_xlabel("Redshift")
    if ylabel is None:
        ylabel = kind
    if ylabel:
        ax.set_ylabel(ylabel)

    return fig, ax
