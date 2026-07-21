import random
from datetime import time


class RandomScheduleStrategy:
    """根据时间范围和最小间隔生成随机提醒时间。"""

    def generate_times(
        self,
        start_time: str,
        end_time: str,
        times_per_day: int,
        minimum_interval: int,
    ) -> list[str]:
        """生成满足最小间隔要求的随机时间。"""

        start = self._parse_time(start_time)
        end = self._parse_time(end_time)

        start_minutes = start.hour * 60 + start.minute
        end_minutes = end.hour * 60 + end.minute

        adjusted_end = (
            end_minutes
            - (times_per_day - 1)
            * (minimum_interval - 1)
        )

        available_values = list(
            range(
                start_minutes,
                adjusted_end + 1,
            )
        )

        if len(available_values) < times_per_day:
            raise ValueError(
                "当前时间范围无法生成满足最小间隔的提醒计划"
            )

        base_values = sorted(
            random.sample(
                available_values,
                times_per_day,
            )
        )

        result_minutes = [
            base_value
            + index * (minimum_interval - 1)
            for index, base_value in enumerate(base_values)
        ]

        return [
            self._format_minutes(value)
            for value in result_minutes
        ]

    @staticmethod
    def _parse_time(value: str) -> time:
        """将 HH:MM 字符串转换为 time 对象。"""

        hour_text, minute_text = value.split(":")

        return time(
            hour=int(hour_text),
            minute=int(minute_text),
        )

    @staticmethod
    def _format_minutes(total_minutes: int) -> str:
        """将分钟数转换为 HH:MM 格式。"""

        hour = total_minutes // 60
        minute = total_minutes % 60

        return f"{hour:02d}:{minute:02d}"