"""Interfaz común de los modelos de pronóstico.

Cada modelo es *stateless* respecto a la serie: recibe el array de precios de
cierre y devuelve el precio pronosticado ``horizon`` pasos adelante. Esto hace
trivial la validación walk-forward (basta con recortar la serie).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class ForecastModel(ABC):
    #: Identificador corto del modelo.
    name: str = "model"
    #: Módulos opcionales que el modelo necesita (vacío = solo numpy).
    requires: tuple[str, ...] = ()

    @abstractmethod
    def forecast(self, prices: np.ndarray, horizon: int) -> float:
        """Pronostica el precio ``horizon`` días después del último dato."""
        raise NotImplementedError
