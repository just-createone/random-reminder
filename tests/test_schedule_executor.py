from backend.executor.schedule_executor import (
    ScheduleExecutor,
)


class FakeScheduleService:
    """测试执行器时使用的计划服务。"""

    def __init__(self) -> None:
        self.enabled = False
        self.schedule_check_count = 0
        self.skip_count = 0

    def is_enabled(self) -> bool:
        return self.enabled

    def get_today_schedule(self) -> list[object]:
        self.schedule_check_count += 1

        return [object()]

    def generate_today_schedule(
        self,
        force: bool = False,
        now=None,
    ) -> list[object]:
        return [object()]

    def skip_overdue_pending(
        self,
        now=None,
        grace_minutes: int = 5,
    ) -> int:
        self.skip_count += 1

        return 0


class FakeNotificationRepository:
    """记录是否查询了待发送通知。"""

    def __init__(self) -> None:
        self.query_count = 0

    def get_due_pending(
        self,
        schedule_date: str,
        current_time: str,
    ) -> list[object]:
        self.query_count += 1

        return []


def test_executor_pauses_and_resumes_with_settings() -> None:
    """总开关应控制整个提醒执行流程。"""

    schedule_service = FakeScheduleService()
    notification_repository = (
        FakeNotificationRepository()
    )

    executor = ScheduleExecutor(
        schedule_service=schedule_service,
        notification_repository=(
            notification_repository
        ),
        notification_service=object(),
        web_push_service=object(),
    )

    # 总开关关闭。
    executor.run_once()

    assert schedule_service.schedule_check_count == 0
    assert schedule_service.skip_count == 0
    assert notification_repository.query_count == 0

    # 重新开启总开关。
    schedule_service.enabled = True

    executor.run_once()

    assert schedule_service.schedule_check_count == 1
    assert schedule_service.skip_count == 1
    assert notification_repository.query_count == 1