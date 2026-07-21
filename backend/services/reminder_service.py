from backend.core.exceptions import ResourceNotFoundError
from backend.domain.reminder import Reminder
from backend.repository.reminder_repository import (
    ReminderRepository,
)


class ReminderService:
    """处理提醒相关的业务规则。"""

    def __init__(
        self,
        repository: ReminderRepository | None = None,
    ) -> None:
        self.repository = repository or ReminderRepository()

    def create_reminder(self, content: str) -> Reminder:
        """检查提醒内容并创建提醒。"""

        cleaned_content = self._validate_content(content)

        return self.repository.create(cleaned_content)

    def get_all_reminders(self) -> list[Reminder]:
        """返回全部提醒。"""

        return self.repository.get_all()

    def get_reminder(self, reminder_id: int) -> Reminder:
        """根据 ID 返回一条提醒。"""

        reminder = self.repository.get_by_id(reminder_id)

        if reminder is None:
            raise ResourceNotFoundError(
                f"ID 为 {reminder_id} 的提醒不存在"
            )

        return reminder

    def update_reminder(
        self,
        reminder_id: int,
        content: str,
    ) -> Reminder:
        """修改提醒内容。"""

        cleaned_content = self._validate_content(content)

        reminder = self.repository.update_content(
            reminder_id=reminder_id,
            content=cleaned_content,
        )

        if reminder is None:
            raise ResourceNotFoundError(
                f"ID 为 {reminder_id} 的提醒不存在"
            )

        return reminder

    def update_reminder_enabled(
        self,
        reminder_id: int,
        enabled: bool,
    ) -> Reminder:
        """启用或停用提醒。"""

        reminder = self.repository.update_enabled(
            reminder_id=reminder_id,
            enabled=enabled,
        )

        if reminder is None:
            raise ResourceNotFoundError(
                f"ID 为 {reminder_id} 的提醒不存在"
            )

        return reminder

    def delete_reminder(self, reminder_id: int) -> None:
        """删除一条提醒。"""

        deleted = self.repository.delete(reminder_id)

        if not deleted:
            raise ResourceNotFoundError(
                f"ID 为 {reminder_id} 的提醒不存在"
            )

    @staticmethod
    def _validate_content(content: str) -> str:
        """清理并检查提醒内容。"""

        cleaned_content = content.strip()

        if not cleaned_content:
            raise ValueError("提醒内容不能为空")

        if len(cleaned_content) > 500:
            raise ValueError("提醒内容不能超过 500 个字符")

        return cleaned_content