import asyncio
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class OrchestratorState(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"

@dataclass
class OrchestratorInstance:
    id: str
    orchestrator: Any # Tutaj EnhancedOrchestrator, ale unikamy cyklicznego importu
    state: OrchestratorState
    last_health_check: float
    failure_count: int = 0

class OrchestratorPool:
    def __init__(self, max_failures: int = 3, health_check_interval: int = 30):
        self.instances: List[OrchestratorInstance] = []
        self.current_index = 0
        self.max_failures = max_failures
        self.health_check_interval = health_check_interval
        self._health_check_task: Optional[asyncio.Task] = None

    async def add_instance(self, orchestrator_id: str, orchestrator: Any):
        """Dodaje instancję orkiestratora do puli."""
        instance = OrchestratorInstance(
            id=orchestrator_id,
            orchestrator=orchestrator,
            state=OrchestratorState.HEALTHY,
            last_health_check=asyncio.get_event_loop().time()
        )
        self.instances.append(instance)
        logger.info(f"Orchestrator instance '{orchestrator_id}' added to pool.")

    async def get_healthy_orchestrator(self) -> Optional[Any]:
        """
        Zwraca kolejny zdrowy orkiestrator z puli, używając algorytmu round-robin.
        Jeśli brak zdrowych, próbuje użyć zdegradowanych.
        """
        healthy_instances = [i for i in self.instances if i.state == OrchestratorState.HEALTHY]

        if not healthy_instances:
            logger.warning("No healthy orchestrator instances available. Trying degraded instances.")
            degraded_instances = [i for i in self.instances if i.state == OrchestratorState.DEGRADED]
            if degraded_instances:
                # W przypadku braku zdrowych, wybierz pierwszy zdegradowany
                return degraded_instances[0].orchestrator
            logger.error("No available orchestrator instances (healthy or degraded).")
            return None

        # Round-robin
        orchestrator_to_return = healthy_instances[self.current_index].orchestrator
        self.current_index = (self.current_index + 1) % len(healthy_instances)
        return orchestrator_to_return

    async def _run_health_checks(self):
        """Cykl przeprowadzania testów zdrowia dla wszystkich instancji."""
        while True:
            for instance in self.instances:
                await self._check_instance_health(instance)
            await asyncio.sleep(self.health_check_interval)

    async def _check_instance_health(self, instance: OrchestratorInstance):
        """Sprawdza zdrowie pojedynczej instancji orkiestratora."""
        try:
            # Wywołaj prostą metodę health_check na orkiestratorze
            # EnhancedOrchestrator musi mieć taką metodę, np. process_command("health_check", ...)
            health_response = await instance.orchestrator.process_command(
                user_command="health_check_internal", session_id=f"health_check_{instance.id}"
            )
            if health_response.get("status") == "ok":
                await self._mark_healthy(instance)
            else:
                await self._mark_failed(instance, f"Health check failed with status: {health_response.get('status')}")
        except Exception as e:
            await self._mark_failed(instance, f"Health check threw exception: {str(e)}")

    async def _mark_healthy(self, instance: OrchestratorInstance):
        if instance.state != OrchestratorState.HEALTHY:
            logger.info(f"Orchestrator '{instance.id}' is now HEALTHY.")
        instance.failure_count = 0
        instance.state = OrchestratorState.HEALTHY
        instance.last_health_check = asyncio.get_event_loop().time()

    async def _mark_failed(self, instance: OrchestratorInstance, reason: str):
        instance.failure_count += 1
        current_time = asyncio.get_event_loop().time()
        
        if instance.failure_count >= self.max_failures and instance.state != OrchestratorState.FAILED:
            instance.state = OrchestratorState.FAILED
            logger.error(f"Orchestrator '{instance.id}' marked as FAILED due to {reason} "
                         f"after {instance.failure_count} failures.")
        elif instance.state != OrchestratorState.DEGRADED:
            instance.state = OrchestratorState.DEGRADED
            logger.warning(f"Orchestrator '{instance.id}' marked as DEGRADED due to {reason}. "
                           f"Failures: {instance.failure_count}/{self.max_failures}.")
        instance.last_health_check = current_time

    async def start_health_checks(self):
        """Uruchamia zadanie w tle do regularnych testów zdrowia."""
        if not self._health_check_task or self._health_check_task.done():
            self._health_check_task = asyncio.create_task(self._run_health_checks())
            logger.info("Orchestrator health checks started.")

    async def shutdown(self):
        """Zatrzymuje zadanie testów zdrowia i zamyka orkiestratory."""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        for instance in self.instances:
            if hasattr(instance.orchestrator, 'shutdown'):
                await instance.orchestrator.shutdown()
        logger.info("Orchestrator pool shut down.")
