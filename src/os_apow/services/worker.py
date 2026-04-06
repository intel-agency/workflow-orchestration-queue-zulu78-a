"""
OS-APOW Sentinel Worker

Orchestrates the execution of work items using the devcontainer-opencode.sh
shell bridge. Manages environment provisioning, task execution, and
heartbeat reporting.
"""

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum

from ..config import get_settings
from ..models.work_item import WorkItem, WorkItemStatus
from .queue import GitHubQueue

logger = logging.getLogger("os_apow.worker")


class WorkerState(str, Enum):
    """State of the sentinel worker."""

    IDLE = "idle"
    PROCESSING = "processing"
    STOPPING = "stopping"
    STOPPED = "stopped"


@dataclass
class WorkerResult:
    """Result of a work item execution."""

    success: bool
    exit_code: int
    stdout: str
    stderr: str
    error_message: str | None = None


class SentinelWorker:
    """Sentinel worker that processes work items.

    Orchestrates the full lifecycle of task execution:
    1. Provision devcontainer environment
    2. Start opencode server
    3. Execute workflow prompt
    4. Report results and update status
    """

    def __init__(self, queue: GitHubQueue):
        """Initialize the sentinel worker.

        Args:
            queue: GitHub queue for status updates.
        """
        self.queue = queue
        self.settings = get_settings()
        self.state = WorkerState.IDLE
        self._current_task: WorkItem | None = None
        self._heartbeat_task: asyncio.Task[None] | None = None
        self._start_time: float = 0

    async def process_task(self, item: WorkItem) -> WorkerResult:
        """Process a single work item.

        Args:
            item: Work item to process.

        Returns:
            WorkerResult with execution details.
        """
        self.state = WorkerState.PROCESSING
        self._current_task = item
        self._start_time = asyncio.get_event_loop().time()

        # Start heartbeat task
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop(item))

        try:
            # Step 1: Provision environment
            logger.info(f"Provisioning environment for task #{item.issue_number}")
            up_result = await self._run_shell_command(["./scripts/devcontainer-opencode.sh", "up"])
            if not up_result.success:
                return WorkerResult(
                    success=False,
                    exit_code=up_result.exit_code,
                    stdout=up_result.stdout,
                    stderr=up_result.stderr,
                    error_message="Failed to provision devcontainer",
                )

            # Step 2: Start opencode server
            logger.info("Starting opencode server")
            start_result = await self._run_shell_command(
                ["./scripts/devcontainer-opencode.sh", "start"]
            )
            if not start_result.success:
                return WorkerResult(
                    success=False,
                    exit_code=start_result.exit_code,
                    stdout=start_result.stdout,
                    stderr=start_result.stderr,
                    error_message="Failed to start opencode server",
                )

            # Step 3: Execute workflow prompt
            logger.info(f"Executing workflow for task #{item.issue_number}")
            prompt_result = await self._run_shell_command(
                ["./scripts/devcontainer-opencode.sh", "prompt"],
                timeout=3600,  # 1 hour max
            )

            return WorkerResult(
                success=prompt_result.success,
                exit_code=prompt_result.exit_code,
                stdout=prompt_result.stdout,
                stderr=prompt_result.stderr,
            )

        finally:
            # Stop heartbeat task
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
                try:
                    await self._heartbeat_task
                except asyncio.CancelledError:
                    pass
                self._heartbeat_task = None

            self._current_task = None
            self.state = WorkerState.IDLE

    async def _run_shell_command(self, command: list[str], timeout: int = 300) -> WorkerResult:
        """Run a shell command asynchronously.

        Args:
            command: Command and arguments to run.
            timeout: Timeout in seconds.

        Returns:
            WorkerResult with command output.
        """
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )

            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")
            exit_code = process.returncode if process.returncode is not None else -1

            return WorkerResult(
                success=exit_code == 0,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
            )

        except TimeoutError:
            return WorkerResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=f"Command timed out after {timeout} seconds",
                error_message="Timeout",
            )
        except Exception as e:
            return WorkerResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                error_message=str(e),
            )

    async def _heartbeat_loop(self, item: WorkItem) -> None:
        """Post periodic heartbeat comments.

        Args:
            item: Work item being processed.
        """
        while True:
            await asyncio.sleep(self.settings.heartbeat_interval_seconds)

            elapsed = int(asyncio.get_event_loop().time() - self._start_time)
            try:
                await self.queue.post_heartbeat(item, self.settings.sentinel_id, elapsed)
            except Exception as e:
                logger.warning(f"Heartbeat failed: {e}")

    async def stop(self) -> None:
        """Gracefully stop the worker.

        Waits for current task to complete before stopping.
        """
        self.state = WorkerState.STOPPING
        logger.info("Worker stopping, waiting for current task to complete")

        # Wait for current task if any
        while self.state == WorkerState.PROCESSING:
            await asyncio.sleep(1)

        self.state = WorkerState.STOPPED
        logger.info("Worker stopped")

    async def finalize_result(self, item: WorkItem, result: WorkerResult) -> None:
        """Update GitHub with the final result.

        Args:
            item: Work item that was processed.
            result: Execution result.
        """
        if result.success:
            await self.queue.update_status(
                item,
                WorkItemStatus.SUCCESS,
                comment=f"✅ **Task completed successfully**\n\n"
                f"- **Exit Code:** {result.exit_code}\n"
                f"- **Sentinel:** {self.settings.sentinel_id}",
            )
        elif result.error_message and "infra" in result.error_message.lower():
            await self.queue.update_status(
                item,
                WorkItemStatus.INFRA_FAILURE,
                comment=f"⚠️ **Infrastructure failure**\n\n"
                f"- **Error:** {result.error_message}\n"
                f"- **Last 50 lines of stderr:**\n```\n"
                f"{result.stderr[-2000:]}\n```",
            )
        else:
            await self.queue.update_status(
                item,
                WorkItemStatus.ERROR,
                comment=f"❌ **Task failed**\n\n"
                f"- **Exit Code:** {result.exit_code}\n"
                f"- **Error:** {result.error_message or 'Unknown'}\n"
                f"- **Sentinel:** {self.settings.sentinel_id}",
            )
