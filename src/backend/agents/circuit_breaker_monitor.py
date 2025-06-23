from typing import Any, Dict, List

from .circuit_breaker_wrapper import AgentCircuitBreaker


class CircuitBreakerMonitor:
    def __init__(self) -> None:
        self.breakers: Dict[str, AgentCircuitBreaker] = {}

    def register_breaker(self, name: str, breaker: AgentCircuitBreaker) -> None:
        """Rejestruje Circuit Breaker do monitorowania."""
        self.breakers[name] = breaker

    def get_health_status(self) -> Dict[str, Any]:
        """Zwraca statusy wszystkich zarejestrowanych Circuit Breakerów."""
        status = {}
        for name, breaker in self.breakers.items():
            status[name] = {
                "state": breaker.get_state(),
                "is_open": breaker.is_open(),
                # Pybreaker nie udostępnia failure_count i last_failure_time bezpośrednio w API CircuitBreaker
                # ale można to rozszerzyć o własne metryki w AgentCircuitBreaker.
            }
        return status

    def get_open_circuits(self) -> List[str]:
        """Zwraca listę nazw otwartych Circuit Breakerów."""
        return [name for name, breaker in self.breakers.items() if breaker.is_open()]
