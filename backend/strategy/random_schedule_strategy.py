import random
from bisect import bisect_left
from datetime import time


class RandomScheduleStrategy:
    """根据时间范围和最小间隔生成随机提醒时间。"""

    def generate_times(
        self,
        start_time: str,
        end_time: str,
        times_per_day: int,
        minimum_interval: int,
        excluded_times: set[str] | None = None,
    ) -> list[str]:
        """
        生成满足时间范围和最小间隔要求的随机时间。

        excluded_times 表示已经被历史计划占用、
        本次不能再次使用的时间。
        """

        if times_per_day < 1:
            raise ValueError(
                "每日提醒次数必须大于 0"
            )

        if minimum_interval < 1:
            raise ValueError(
                "最小提醒间隔必须大于 0"
            )

        start = self._parse_time(start_time)
        end = self._parse_time(end_time)

        start_minutes = (
            start.hour * 60
            + start.minute
        )

        end_minutes = (
            end.hour * 60
            + end.minute
        )

        if end_minutes < start_minutes:
            raise ValueError(
                "提醒结束时间必须晚于开始时间"
            )

        excluded_values = {
            self._time_to_minutes(
                self._parse_time(value)
            )
            for value in (
                excluded_times
                or set()
            )
        }

        available_values = [
            value
            for value in range(
                start_minutes,
                end_minutes + 1,
            )
            if value not in excluded_values
        ]

        result_minutes = self._find_times(
            candidates=available_values,
            count=times_per_day,
            minimum_interval=minimum_interval,
        )

        if result_minutes is None:
            raise ValueError(
                "当前时间范围无法生成满足最小间隔的提醒计划"
            )

        return [
            self._format_minutes(value)
            for value in result_minutes
        ]

    @staticmethod
    def _find_times(
        candidates: list[int],
        count: int,
        minimum_interval: int,
    ) -> list[int] | None:
        """使用回溯算法寻找一组有效提醒时间。"""

        failed_states: set[
            tuple[int, int]
        ] = set()

        def search(
            start_index: int,
            remaining_count: int,
        ) -> list[int] | None:
            if remaining_count == 0:
                return []

            state = (
                start_index,
                remaining_count,
            )

            if state in failed_states:
                return None

            remaining_candidates = (
                len(candidates)
                - start_index
            )

            if (
                remaining_candidates
                < remaining_count
            ):
                failed_states.add(state)
                return None

            latest_first_value = (
                candidates[-1]
                - (
                    remaining_count - 1
                )
                * minimum_interval
            )

            possible_indices = [
                index
                for index in range(
                    start_index,
                    len(candidates),
                )
                if (
                    candidates[index]
                    <= latest_first_value
                )
            ]

            random.shuffle(
                possible_indices
            )

            for index in possible_indices:
                current_value = (
                    candidates[index]
                )

                next_minimum_value = (
                    current_value
                    + minimum_interval
                )

                next_index = bisect_left(
                    candidates,
                    next_minimum_value,
                    lo=index + 1,
                )

                tail = search(
                    start_index=next_index,
                    remaining_count=(
                        remaining_count - 1
                    ),
                )

                if tail is not None:
                    return [
                        current_value,
                        *tail,
                    ]

            failed_states.add(state)

            return None

        return search(
            start_index=0,
            remaining_count=count,
        )

    @staticmethod
    def _parse_time(
        value: str,
    ) -> time:
        """将 HH:MM 字符串转换为 time 对象。"""

        hour_text, minute_text = (
            value.split(":")
        )

        return time(
            hour=int(hour_text),
            minute=int(minute_text),
        )

    @staticmethod
    def _time_to_minutes(
        value: time,
    ) -> int:
        """把 time 转换为当天总分钟数。"""

        return (
            value.hour * 60
            + value.minute
        )

    @staticmethod
    def _format_minutes(
        total_minutes: int,
    ) -> str:
        """将分钟数转换为 HH:MM 格式。"""

        hour = total_minutes // 60
        minute = total_minutes % 60

        return (
            f"{hour:02d}:"
            f"{minute:02d}"
        )