"""NLP 时间解析模块。

提供自然语言时间解析功能，支持中文时间表达。
包括相对时间、绝对时间、时间段、重复规则的解析。

Author: Claude Code
Date: 2026-02-06
"""

from datetime import datetime, timedelta, time
from typing import Optional, Dict, Any, Tuple
import re
from dateutil import parser
from dateutil.relativedelta import relativedelta

from src.utils.logger import get_logger

logger = get_logger(__name__)


class DateTimeParser:
    """日期时间解析器。

    支持中文时间表达解析，包括相对时间、绝对时间、时间段等。
    """

    # 中文时间关键词映射
    TIME_KEYWORDS = {
        "明天": 1,
        "后天": 2,
        "大后天": 3,
        "今天": 0,
        "昨日": -1,
        "前天": -2,
        "下周": 7,
        "下周同一时间": 7,
        "下周今天": 7,
        "下下周": 14,
    }

    # 星期映射
    WEEKDAY_MAPPING = {
        "周一": 0,
        "周二": 1,
        "周三": 2,
        "周四": 3,
        "周五": 4,
        "周六": 5,
        "周日": 6,
        "星期一": 0,
        "星期二": 1,
        "星期三": 2,
        "星期四": 3,
        "星期五": 4,
        "星期六": 5,
        "星期日": 6,
        "礼拜一": 0,
        "礼拜二": 1,
        "礼拜三": 2,
        "礼拜四": 3,
        "礼拜五": 4,
        "礼拜六": 5,
        "礼拜日": 6,
    }

    # 时段映射
    TIME_PERIODS = {
        "早上": (8, 0),
        "上午": (9, 0),
        "中午": (12, 0),
        "下午": (14, 0),
        "傍晚": (18, 0),
        "晚上": (19, 0),
        "夜里": (21, 0),
        "深夜": (23, 0),
        "凌晨": (2, 0),
    }

    # 时间单位映射
    TIME_UNITS = {
        "秒": "seconds",
        "分钟": "minutes",
        "小时": "hours",
        "天": "days",
        "周": "weeks",
        "月": "months",
        "年": "years",
    }

    def __init__(self) -> None:
        """初始化日期时间解析器。"""
        self.current_time = datetime.now()

    def parse(self, text: str) -> Optional[datetime]:
        """解析日期时间。

        Args:
            text: 时间文本，如"明天下午3点"、"2024-02-10 15:00"

        Returns:
            解析后的 datetime 对象，解析失败返回 None

        Examples:
            >>> parser = DateTimeParser()
            >>> dt = parser.parse("明天下午3点")
            >>> print(dt.strftime("%Y-%m-%d %H:%M"))
        """
        if not text or not text.strip():
            logger.warning("Empty input text")
            return None

        text = text.strip()
        logger.info(f"Parsing datetime: {text}")

        # 1. 尝试解析相对时间（明天、下周等）
        result = self._parse_relative_time(text)
        if result:
            return result

        # 2. 尝试解析星期（下周一、本周三）
        result = self._parse_weekday(text)
        if result:
            return result

        # 3. 尝试使用 dateutil 解析绝对时间
        result = self._parse_absolute_time(text)
        if result:
            return result

        # 4. 尝试解析时段（下午3点 -> 15:00）
        result = self._parse_time_with_period(text)
        if result:
            return result

        logger.warning(f"Failed to parse datetime: {text}")
        return None

    def _parse_relative_time(self, text: str) -> Optional[datetime]:
        """解析相对时间。

        Args:
            text: 包含相对关键词的文本

        Returns:
            解析后的 datetime，失败返回 None
        """
        for keyword, days in self.TIME_KEYWORDS.items():
            if keyword in text:
                result = self.current_time + timedelta(days=days)

                # 尝试提取具体时间
                time_match = re.search(r"(\d{1,2})点((\d{1,2})分)?", text)
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(3)) if time_match.group(3) else 0

                    # 根据时段调整小时
                    # 如果是"下午"或"晚上"，且小时<12，则加12（3点下午=15点）
                    if any(p in text for p in ["下午", "晚上", "傍晚", "夜里", "深夜"]) and hour < 12:
                        hour += 12
                    # 如果是"凌晨"，且小时>=12，则减12（凌晨2点=2点，不是14点）
                    elif "凌晨" in text and hour >= 12:
                        hour -= 12

                    result = result.replace(hour=hour, minute=minute)
                else:
                    # 没有具体时间数字，使用时段默认时间
                    for period, (hour, minute) in self.TIME_PERIODS.items():
                        if period in text:
                            result = result.replace(hour=hour, minute=minute)
                            break

                logger.info(f"Parsed relative time '{keyword}': {result}")
                return result

        return None

    def _parse_weekday(self, text: str) -> Optional[datetime]:
        """解析星期。

        Args:
            text: 包含星期的文本

        Returns:
            解析后的 datetime，失败返回 None
        """
        for weekday_name, weekday_num in self.WEEKDAY_MAPPING.items():
            if weekday_name in text or "下周" + weekday_name in text:
                # 计算目标星期
                current_weekday = self.current_time.weekday()
                days_ahead = weekday_num - current_weekday

                if days_ahead <= 0:  # 目标星期在本周已过
                    days_ahead += 7

                if "下周" in text:
                    days_ahead += 7

                result = self.current_time + timedelta(days=days_ahead)

                # 尝试提取时间
                time_match = re.search(r"(\d{1,2})点((\d{1,2})分)?", text)
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(3)) if time_match.group(3) else 0
                    result = result.replace(hour=hour, minute=minute)
                else:
                    # 检查时段
                    for period, (hour, minute) in self.TIME_PERIODS.items():
                        if period in text:
                            result = result.replace(hour=hour, minute=minute)
                            break

                logger.info(f"Parsed weekday '{weekday_name}': {result}")
                return result

        return None

    def _parse_absolute_time(self, text: str) -> Optional[datetime]:
        """解析绝对时间。

        Args:
            text: 绝对时间文本

        Returns:
            解析后的 datetime，失败返回 None
        """
        try:
            # 检查是否是标准的日期时间格式
            # 如果只是"下午3点"这种格式，不使用dateutil，留给_parse_time_with_period处理
            has_date_format = bool(re.search(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', text))
            has_time_format = bool(re.search(r'\d{1,2}:\d{2}', text))
            has_chinese_date = any(w in text for w in ["年", "月", "日"])

            # 如果没有明确的日期格式，跳过
            if not has_date_format and not has_chinese_date:
                logger.debug(f"No clear date format found, skipping absolute time parsing")
                return None

            # 移除中文文字，尝试使用 dateutil 解析
            cleaned_text = re.sub(r"[^\d\s\-/:年月日时分秒]", " ", text)
            cleaned_text = cleaned_text.replace("年", "-").replace("月", "-").replace("日", " ")
            cleaned_text = cleaned_text.replace("时", ":").replace("分", ":").replace("秒", "")

            result = parser.parse(cleaned_text, fuzzy=True)

            logger.info(f"Parsed absolute time: {result}")
            return result

        except (ValueError, parser.ParserError) as e:
            logger.debug(f"Failed to parse absolute time: {e}")
            return None

    def _parse_time_with_period(self, text: str) -> Optional[datetime]:
        """解析带时段的时间。

        Args:
            text: 包含时段的文本

        Returns:
            解析后的 datetime，失败返回 None
        """
        for period, (default_hour, default_minute) in self.TIME_PERIODS.items():
            if period in text:
                # 提取具体时间
                time_match = re.search(r"(\d{1,2})点((\d{1,2})分)?", text)
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(3)) if time_match.group(3) else 0

                    # 根据时段调整小时
                    # 如果是"下午"或"晚上"，且小时<12，则加12
                    if any(p in text for p in ["下午", "晚上", "傍晚", "夜里", "深夜"]) and hour < 12:
                        hour += 12
                    # 如果是"凌晨"，且小时>=12，则减12
                    elif "凌晨" in text and hour >= 12:
                        hour -= 12
                else:
                    # 没有具体时间，使用时段默认时间
                    hour = default_hour
                    minute = default_minute

                result = self.current_time.replace(hour=hour, minute=minute)
                logger.info(f"Parsed time with period '{period}': {result}")
                return result

        return None


class RecurrenceParser:
    """重复规则解析器。

    解析重复规则，如"每天早上9点"、"每周一下午2点"。
    """

    # 重复频率关键词
    FREQUENCY_KEYWORDS = {
        "每天": "daily",
        "每日": "daily",
        "每周": "weekly",
        "每星期": "weekly",
        "每月": "monthly",
        "每年": "yearly",
    }

    def __init__(self) -> None:
        """初始化重复规则解析器。"""
        self.datetime_parser = DateTimeParser()

    def parse(self, text: str) -> Optional[Dict[str, Any]]:
        """解析重复规则。

        Args:
            text: 包含重复规则的文本

        Returns:
            重复规则字典，包含：
            - frequency: 频率 (daily/weekly/monthly/yearly)
            - start_time: 开始时间
            - end_time: 结束时间（可选）
            失败返回 None

        Examples:
            >>> parser = RecurrenceParser()
            >>> rule = parser.parse("每天早上9点提醒我喝水")
            >>> print(rule)
        """
        if not text or not text.strip():
            return None

        text = text.strip()
        logger.info(f"Parsing recurrence: {text}")

        # 1. 识别频率
        frequency = None
        for keyword, freq in self.FREQUENCY_KEYWORDS.items():
            if keyword in text:
                frequency = freq
                break

        if not frequency:
            logger.debug("No frequency keyword found")
            return None

        # 2. 解析开始时间
        start_time = self.datetime_parser.parse(text)
        if not start_time:
            logger.warning("Failed to parse start time for recurrence")
            return None

        # 3. 构建重复规则
        rule = {
            "frequency": frequency,
            "start_time": start_time,
        }

        # 4. 尝试解析结束条件
        # 例如："持续一个月"、"直到下个月底"
        # （简化版本，暂不实现）

        logger.info(f"Parsed recurrence rule: {rule}")
        return rule


class EventExtractor:
    """事件信息提取器。

    从自然语言文本中提取事件信息，包括标题、时间、描述等。
    """

    # 动词关键词（表示创建/提醒）
    ACTION_KEYWORDS = [
        "提醒",
        "安排",
        "预约",
        "预定",
        "设置",
        "创建",
        "添加",
        "记下",
    ]

    # 时间连接词
    TIME_CONNECTORS = [
        "在",
        "于",
        "到",
        "从",
        "自",
    ]

    def __init__(self) -> None:
        """初始化事件提取器。"""
        self.datetime_parser = DateTimeParser()

    def extract(self, text: str) -> Optional[Dict[str, Any]]:
        """提取事件信息。

        Args:
            text: 事件文本，如"提醒我明天下午3点开会"

        Returns:
            事件信息字典，包含：
            - title: 事件标题
            - start_time: 开始时间
            - end_time: 结束时间（可选）
            - description: 描述（可选）
            失败返回 None

        Examples:
            >>> extractor = EventExtractor()
            >>> event = extractor.extract("提醒我明天下午3点开会")
            >>> print(event)
        """
        if not text or not text.strip():
            return None

        text = text.strip()
        logger.info(f"Extracting event from: {text}")

        result = {}

        # 1. 提取时间
        time_match = self._extract_time(text)
        if not time_match:
            logger.warning("No time found in text")
            return None

        result["start_time"] = time_match

        # 2. 移除时间关键词，提取标题
        title_text = self._remove_time_keywords(text)
        result["title"] = self._extract_title(title_text)

        # 3. 提取描述（可选）
        # （简化版本，暂不实现）

        logger.info(f"Extracted event: {result}")
        return result

    def _extract_time(self, text: str) -> Optional[datetime]:
        """提取时间。

        Args:
            text: 文本

        Returns:
            提取的时间，失败返回 None
        """
        return self.datetime_parser.parse(text)

    def _remove_time_keywords(self, text: str) -> str:
        """移除时间关键词。

        Args:
            text: 原始文本

        Returns:
            移除时间后的文本
        """
        result = text

        # 移除动作关键词
        for keyword in self.ACTION_KEYWORDS:
            result = result.replace(keyword, "")

        # 移除时间连接词
        for keyword in self.TIME_CONNECTORS:
            result = result.replace(keyword, "")

        # 移除时间表达（简化处理）
        # （更复杂的处理需要使用正则表达式匹配时间模式）

        # 移除"我"、"帮我"等
        result = result.replace("我", "").replace("帮我", "").replace("帮", "")

        return result.strip()

    def _extract_title(self, text: str) -> str:
        """提取标题。

        Args:
            text: 移除时间后的文本

        Returns:
            事件标题
        """
        if not text:
            return "未命名事件"

        # 取前20个字符作为标题
        title = text[:20]

        # 移除标点符号
        title = re.sub(r"[，。！？、；：]", "", title)

        return title.strip()


# 便捷函数
def parse_datetime(text: str) -> Optional[datetime]:
    """解析日期时间（便捷函数）。

    Args:
        text: 时间文本

    Returns:
        解析后的 datetime 对象
    """
    parser = DateTimeParser()
    return parser.parse(text)


def parse_recurrence(text: str) -> Optional[Dict[str, Any]]:
    """解析重复规则（便捷函数）。

    Args:
        text: 包含重复规则的文本

    Returns:
        重复规则字典
    """
    parser = RecurrenceParser()
    return parser.parse(text)


def extract_event_info(text: str) -> Optional[Dict[str, Any]]:
    """提取事件信息（便捷函数）。

    Args:
        text: 事件文本

    Returns:
        事件信息字典
    """
    extractor = EventExtractor()
    return extractor.extract(text)
