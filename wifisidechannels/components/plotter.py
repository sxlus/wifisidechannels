import numpy as np
import matplotlib as plt
import typing

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
            data: list[list[int | float]] | list[float | int],
            size: tuple = (20,10),
            msg: str = "",
            plot: bool = False,
            scatter: bool = False
    ) -> np.ndarray:

        if not isinstance(data, list) or not data:
            print(f"{self.m_name} [ERROR] Data not plotable {str(data)} ")
            return None
        
        if not isinstance(data[0], list):
            domain      = np.arange(start=0, stop=len(data))
            codomain    = np.ndarray(data)
        else:
            sorted_data = sorted(data, key = lambda x: x[0])
            domain = np.ndarray([x[0] for x in sorted_data])
            codomain = np.ndarray([x[1] for x in sorted_data])
        
        plt.rcParams["figure.figsize"] = size
        plt.title(f"Plotting function: {msg}")
        plt.xlim([ np.min(domain)   , np.max(domain) ])
        plt.ylim([ np.min(codomain) , np.max(codomain) ])

        if scatter:
            plt.scatter(domain, codomain, c = np.random.rand(domain.shape[0]), s = (30 * np.random.rand(domain.shape[0]))**2, alpha=0.5)
        else:
            plt.plot(domain, codomain)
        if plot:
            plt.show()

        return codomain