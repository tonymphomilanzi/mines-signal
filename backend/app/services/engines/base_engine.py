from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.model import SignalModel
from app.models.signal import Signal


@dataclass
class EnginePrediction:
    """
    Standard prediction returned by every prediction engine.

    All engines must return this same structure so the rest of
    the signal system does not need to know which engine produced it.
    """

    safe_positions: list[int]
    predicted_mine_positions: list[int]
    confidence: float | None

    @property
    def recommended_positions(self) -> list[int]:
        return self.safe_positions


class BaseEngine(ABC):
    """
    Base contract for all Mines prediction engines.

    Future engines:
        StatisticalEngine
        PatternEngine
        MLEngine
    """

    name = "base"
    version = "1.0.0"

    @abstractmethod
    def predict(
        self,
        db: Session,
        signal: Signal,
        model: SignalModel,
    ) -> EnginePrediction:
        """
        Generate a prediction for a signal.

        Implementations must not modify the Signal directly.
        They should only calculate and return an EnginePrediction.
        """
        raise NotImplementedError