import pandas as pd
import numpy as np
from dataclasses import dataclass
from abc import ABC, abstractmethod


class StochasticProcess(ABC):
    """Represente a stocastic process (just for typing)"""

    @abstractmethod
    def simulate(self):
        ...


@dataclass
class GeometricBrownianMotion(StochasticProcess):
    """
    A classic geometric brownian motion which can be simulated.
    The closed form formula allow a fully vectorized calculation of the paths.
    """

    mu: float
    sigma: float

    def simulate(
        self,
        s0: float,
        T: int,
        n: int,
        m: int,
        v0: float = None,
        antithetic: bool = False,
        seed: int = None,
    ) -> pd.DataFrame:  # n = number of path, m = number of discretization points

        if seed:
            np.random.seed(seed)

        signe = -1 if antithetic else 1

        dt = T / m
        W = signe * np.cumsum(np.sqrt(dt) * np.random.randn(m + 1, n), axis=0)
        W[0] = 0

        T = np.ones(n).reshape(1, -1) * np.linspace(0, T, m + 1).reshape(-1, 1)

        s = s0 * np.exp((self.mu - 0.5 * self.sigma ** 2) * T + self.sigma * W)

        return s


@dataclass
class HestonProcess(StochasticProcess):
    """
    An Heston process which can be simulated using Milstein schema.
    """

    mu: float
    kappa: float
    theta: float
    eta: float
    rho: float
    milstein: bool = True

    def simulate(
        self,
        s0: float,
        v0: float,
        T: int,
        n: int,
        m: int,
        return_vol: bool = False,
        antithetic: bool = False,
        seed: int = None,
    ) -> pd.DataFrame:  # n = number of path, m = number of discretization points

        if seed:
            np.random.seed(seed)

        dt = T / m
        z1 = np.random.randn(m, n)
        z2 = self.rho * z1 + np.sqrt(1 - self.rho ** 2) * np.random.randn(m, n)

        signe = -1 if antithetic else 1
        z1, z2 = z1 * signe, z2 * signe

        s = np.zeros((m + 1, n))
        x = np.zeros((m + 1, n))
        v = np.zeros((m + 1, n))

        s[0] = s0
        v[0] = v0

        for i in range(m):

            v[i + 1] = (
                v[i]
                + self.kappa * (self.theta - v[i]) * dt
                + self.eta * np.sqrt(v[i] * dt) * z1[i]
                + (self.eta ** 2 / 4 * (z1[i] ** 2 - 1) * dt if self.milstein else 0)
            )
            v = np.where(v > 0, v, -v)

            x[i + 1] = x[i] + (self.mu - v[i] / 2) * dt + np.sqrt(v[i] * dt) * z2[i]

            s[1:] = s[0] * np.exp(x[1:])

        return s if not return_vol else (s, v)
