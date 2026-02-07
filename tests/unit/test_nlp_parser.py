"""NLP 时间解析模块单元测试。

测试 DateTimeParser、RecurrenceParser、EventExtractor 的功能。

Author: Claude Code
Date: 2026-02-06
"""

import pytest
from datetime import datetime, timedelta

from src.utils.nlp import (
    DateTimeParser,
    RecurrenceParser,
    EventExtractor,
    parse_datetime,
    parse_recurrence,
    extract_event_info,
)


class TestDateTimeParser:
    """DateTimeParser 测试类。"""

    def setup_method(self):
        """测试前设置。"""
        self.parser = DateTimeParser()

    def test_parse_tomorrow(self):
        """测试解析"明天"。"""
        result = self.parser.parse("明天下午3点开会")
        assert result is not None
        expected = datetime.now() + timedelta(days=1)
        assert result.date() == expected.date()
        assert result.hour == 15

    def test_parse_relative_time(self):
        """测试解析相对时间。"""
        result = self.parser.parse("后天上午10点")
        assert result is not None
        expected = datetime.now() + timedelta(days=2)
        assert result.date() == expected.date()
        assert result.hour == 10

    def test_parse_absolute_time(self):
        """测试解析绝对时间。"""
        result = self.parser.parse("2026-02-10 15:00")
        assert result is not None
        assert result.year == 2026
        assert result.month == 2
        assert result.day == 10
        assert result.hour == 15

    def test_parse_time_with_period(self):
        """测试解析带时段的时间。"""
        result = self.parser.parse("下午3点")
        assert result is not None
        assert result.hour == 15  # 下午3点 = 15点（3 + 12）

    def test_parse_empty_input(self):
        """测试空输入。"""
        result = self.parser.parse("")
        assert result is None

    def test_parse_invalid_input(self):
        """测试无效输入。"""
        result = self.parser.parse("这是一个没有时间的句子")
        assert result is None


class TestRecurrenceParser:
    """RecurrenceParser 测试类。"""

    def setup_method(self):
        """测试前设置。"""
        self.parser = RecurrenceParser()

    def test_parse_daily_recurrence(self):
        """测试解析"每天"。"""
        result = self.parser.parse("每天早上9点提醒我喝水")
        assert result is not None
        assert result["frequency"] == "daily"
        assert "start_time" in result

    def test_parse_weekly_recurrence(self):
        """测试解析"每周"。"""
        result = self.parser.parse("每周一下午2点开会")
        assert result is not None
        assert result["frequency"] == "weekly"

    def test_parse_empty_input(self):
        """测试空输入。"""
        result = self.parser.parse("")
        assert result is None

    def test_parse_no_frequency(self):
        """测试没有频率关键词。"""
        result = self.parser.parse("明天下午3点")
        assert result is None


class TestEventExtractor:
    """EventExtractor 测试类。"""

    def setup_method(self):
        """测试前设置。"""
        self.extractor = EventExtractor()

    def test_extract_simple_event(self):
        """测试提取简单事件。"""
        result = self.extractor.extract("提醒我明天下午3点开会")
        assert result is not None
        assert "title" in result
        assert "start_time" in result
        assert "开会" in result["title"]

    def test_extract_event_with_description(self):
        """测试提取带描述的事件。"""
        result = self.extractor.extract("明天下午3点开会讨论项目进度")
        assert result is not None
        assert result["title"] is not None

    def test_extract_empty_input(self):
        """测试空输入。"""
        result = self.extractor.extract("")
        assert result is None

    def test_extract_event_without_time(self):
        """测试没有时间的事件。"""
        result = self.extractor.extract("提醒我开会")
        assert result is None


class TestConvenienceFunctions:
    """便捷函数测试类。"""

    def test_parse_datetime_convenience(self):
        """测试 parse_datetime 便捷函数。"""
        result = parse_datetime("明天下午3点")
        assert result is not None

    def test_parse_recurrence_convenience(self):
        """测试 parse_recurrence 便捷函数。"""
        result = parse_recurrence("每天早上9点")
        assert result is not None

    def test_extract_event_info_convenience(self):
        """测试 extract_event_info 便捷函数。"""
        result = extract_event_info("提醒我明天下午3点开会")
        assert result is not None
