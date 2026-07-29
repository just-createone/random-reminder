from backend.executor.schedule_executor import (
    ScheduleExecutor,
)


class FakeScheduleService:
    """用于测试总开关行为。"""

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
    """记录执行器是否查询了到期通知。"""

    def __init__(self) -> None:
        self.query_count = 0

    def get_due_pending(
        self,
        schedule_date: str,
        current_time: str,
    ) -> list[object]:
        self.query_count += 1
        return []


def main() -> None:
    schedule_service = FakeScheduleService()
    notification_repository = (
        FakeNotificationRepository()
    )

    executor = ScheduleExecutor(
        schedule_service=schedule_service,
        notification_repository=(
            notification_repository
        ),
        notifier=object(),
        web_push_service=object(),
    )

    # 总开关关闭：不能检查计划和通知。
    executor.run_once()

    assert (
        schedule_service.schedule_check_count
        == 0
    )
    assert schedule_service.skip_count == 0
    assert (
        notification_repository.query_count
        == 0
    )

    print(
        {
            "disabled_schedule_checks": (
                schedule_service
                .schedule_check_count
            ),
            "disabled_due_queries": (
                notification_repository
                .query_count
            ),
        }
    )

    # 总开关开启：恢复正常检查。
    schedule_service.enabled = True

    executor.run_once()

    assert (
        schedule_service.schedule_check_count
        == 1
    )
    assert schedule_service.skip_count == 1
    assert (
        notification_repository.query_count
        == 1
    )

    print(
        {
            "enabled_schedule_checks": (
                schedule_service
                .schedule_check_count
            ),
            "enabled_due_queries": (
                notification_repository
                .query_count
            ),
        }
    )

    print("执行器暂停和恢复测试通过")


if __name__ == "__main__":
    main()
    