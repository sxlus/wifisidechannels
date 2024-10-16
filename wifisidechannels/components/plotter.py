import numpy as np
import matplotlib.pyplot as plt
import matplotlib.axes as axes
import typing
import pathlib


class Plotter():
    """
    Can plot stuff
    """
    m_name: str     = "[plotter]"
    def plot_func(
            func: typing.Callable,
            drange: np.ndarray = np.arange(-10, 11, 0.1),
            size: tuple = (20,10),
            msg: str = "",
            plot: bool = False,
            scatter: bool = False
    ) -> np.ndarray:

        plt.rcParams["figure.figsize"] = size
        plt.title(f"Plotting function: {msg}")
        domain = drange
        codomain: typing.Iterable = func(domain)
        plt.xlim([ np.min(domain)   , np.max(domain) ])
        plt.ylim([ np.min(codomain) , np.max(codomain) ])

        if scatter:
            plt.scatter(domain, codomain, c = np.random.rand(domain.shape[0]), s = (30 * np.random.rand(domain.shape[0]))**2, alpha=0.5)
        else:
            plt.plot(domain, codomain)
        if plot:
            plt.show()

        return codomain

    def plot_data(
            self,
            data: list[list[int | float]] | list[float | int] | list[list[list[int | float]] | list[float | int]],
            size: tuple = (20,10),
            msg: str | list[str] = "",
            plot: bool = False,
            scatter: bool = False,
            imshow: bool = False,
            label: str | list   = None,
            subplots: bool = False,
            ax: axes.Axes = None,
            save_file: str | pathlib.Path = None,
            dpi: int = 200,
            xlabel: str | list[str] = None,
            ylabel: str | list[str] = None,
            window_title: str = None,
            figure = None
    ) -> np.ndarray:
        if not isinstance(data, list) or not data:
            print(f"{self.m_name} [ERROR] Data not plotable {str(data)} ")
            return None
        if subplots is True and ax is None:
            plt.rcParams["figure.figsize"] = size
            fig, axs = plt.subplots(len(data), 1, sharex="row")
            # does not work
            #plt.title(window_title)
            for idx in range(len(data)):
                self.plot_data(
                    data=data[idx],
                    size=size,
                    msg=msg[idx] if (isinstance(msg, list) and idx < len(msg)) else str(msg) if msg is not None else None,
                    plot=False,
                    scatter=scatter,
                    label=label[idx] if (isinstance(label, list) and idx < len(label)) else str(label) if label is not None else None,
                    subplots=True,
                    ax=axs[idx],
                    xlabel=xlabel[idx] if (isinstance(xlabel, list) and idx < len(xlabel)) else str(xlabel) if ((xlabel is not None) and (idx == (len(data)-1))) else None,
                    ylabel=ylabel[idx] if (isinstance(ylabel, list) and idx < len(ylabel)) else str(ylabel) if ylabel is not None else None,
                    imshow=imshow,
                    figure = fig
                )

            if plot is True:
                #plt.title(f"Plotting: {msg}")
                #plt.legend()
                fig.tight_layout()
                fig.subplots_adjust(top=0.88)
                plt.show()
            if save_file is not None:
                fig.savefig(str(save_file), dpi = dpi)
            return
        if not imshow:
            if not isinstance(data[0], list):
                domain      = np.arange(start=0, stop=len(data))
                codomain    = np.array(data)
            else:
                sorted_data = sorted(data, key = lambda x: x[0])
                domain      = np.array([i[0] for i in sorted_data])
                codomain    = np.array([x[1] for x in sorted_data])
                #print(domain)
        else:
            codomain = data
        plt.rcParams["figure.figsize"] = size
        if ax:
            sp = ax
            sp.set(
                xlabel=xlabel,
                ylabel=ylabel,
                title=msg
            )
        else:
            sp = plt
            figure = sp.figure()
            sp.title(f"Plotting: {msg}")
            plt.xlabel(xlabel=xlabel)
            plt.ylabel(ylabel=ylabel)
            #cxliml, cxlimr = plt.xlim()
            #plt.xlim(**{
            #    "left":     min(cxliml, min(domain)),
            #    "right":    max(cxlimr, max(domain))
            #    }
            #)
            #cyliml, cylimr = plt.ylim()
            #plt.ylim(**{
            #    "bottom":     min(cyliml, min(codomain)),
            #    "top":        max(cylimr, max(codomain))
            #    }
            #)


        if scatter:
            sp.scatter(domain, codomain, c = np.random.rand(domain.shape[0]), s = (30 * np.random.rand(domain.shape[0]))**2, alpha=0.5, label=("" if not label else str(label)))
            if subplots is True and ax is not None:
                sp.legend()
        elif imshow:
            #pcm = sp.imshow(codomain, cmap='viridis', aspect='auto')
            pcm = sp.pcolormesh(np.real(codomain), cmap='viridis', linewidth=0, rasterized=True)
            figure.colorbar(pcm, ax = sp if sp != plt else None)

        else:
            sp.plot(
                codomain,
                label=("" if not label else str(label))
            )
            if subplots is True and ax is not None and label is not None:
                sp.legend()
        if save_file is not None:
            plt.savefig(str(save_file), dpi = dpi)
            if plot is False:
                plt.clf()
        if plot:
            plt.show()
        return codomain