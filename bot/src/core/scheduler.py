import logging
from typing import Callable, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


class TaskScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    async def start(self):
        """Inicia o scheduler de tarefas."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Task Scheduler iniciado com sucesso")

    async def stop(self):
        """Para o scheduler de tarefas."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Task Scheduler parado com sucesso")

    def schedule_daily_task(self, func: Callable, hour: int, minute: int = 0, job_id: Optional[str] = None):
        """
        Agenda uma tarefa para executar diariamente em uma hora específica.

        Args:
            func: Função assincronista a executar
            hour: Hora (0-23)
            minute: Minuto (0-59)
            job_id: ID único da tarefa (opcional)
        """
        job_id = job_id or f"daily_{hour}_{minute}_{func.__name__}"

        # Remove job anterior se existir
        existing_job = self.scheduler.get_job(job_id)
        if existing_job:
            existing_job.remove()

        self.scheduler.add_job(
            func,
            trigger=CronTrigger(hour=hour, minute=minute),
            id=job_id,
            name=f"Daily task at {hour:02d}:{minute:02d} - {func.__name__}",
            replace_existing=True,
        )

        logger.info(f"Tarefa agendada: {job_id} às {hour:02d}:{minute:02d}")

    def schedule_interval_task(self, func: Callable, hours: int = 1, minutes: int = 0, job_id: Optional[str] = None):
        """
        Agenda uma tarefa para executar periodicamente.

        Args:
            func: Função assincronista a executar
            hours: Intervalo em horas
            minutes: Intervalo em minutos adicional
            job_id: ID único da tarefa (opcional)
        """
        job_id = job_id or f"interval_{func.__name__}"

        # Remove job anterior se existir
        existing_job = self.scheduler.get_job(job_id)
        if existing_job:
            existing_job.remove()

        self.scheduler.add_job(
            func,
            "interval",
            hours=hours,
            minutes=minutes,
            id=job_id,
            name=f"Interval task every {hours}h {minutes}m - {func.__name__}",
            replace_existing=True,
        )

        logger.info(f"Tarefa agendada: {job_id} a cada {hours}h {minutes}m")

    def remove_job(self, job_id: str):
        """Remove uma tarefa agendada."""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.remove()
                logger.info(f"Tarefa removida: {job_id}")
            else:
                logger.warning(f"Tarefa não encontrada: {job_id}")
        except Exception as e:
            logger.error(f"Erro ao remover tarefa {job_id}: {e}")

    def list_jobs(self):
        """Retorna lista de todas as tarefas agendadas."""
        return self.scheduler.get_jobs()

    def get_job(self, job_id: str):
        """Retorna uma tarefa específica."""
        return self.scheduler.get_job(job_id)
