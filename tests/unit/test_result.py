#!/usr/bin/env python3
"""
测试 Result 类
"""

from modules.utils.result import Result, StatusCode, ok, fail, warning


class TestResult:
    """测试 Result 类"""

    def test_result_ok(self):
        """测试成功结果"""
        result = Result.ok(data={"key": "value"}, message="测试成功")

        assert result.code == StatusCode.SUCCESS
        assert result.message == "测试成功"
        assert result.data == {"key": "value"}
        assert result.error_code is None
        assert result.is_success is True
        assert result.is_error is False

    def test_result_fail(self):
        """测试失败结果"""
        result = Result.fail(
            error_code="TEST_ERROR", message="测试失败", data={"detail": "错误详情"}
        )

        assert result.code == StatusCode.ERROR
        assert result.message == "测试失败"
        assert result.data == {"detail": "错误详情"}
        assert result.error_code == "TEST_ERROR"
        assert result.is_success is False
        assert result.is_error is True

    def test_result_warning(self):
        """测试警告结果"""
        result = Result.warning(message="测试警告", data={"level": "low"})

        assert result.code == StatusCode.WARNING
        assert result.message == "测试警告"
        assert result.data == {"level": "low"}
        assert result.is_warning is True

    def test_result_to_dict(self):
        """测试转换为字典"""
        result = Result.ok(data={"order_id": "123"})
        result_dict = result.to_dict()

        assert result_dict["code"] == "success"
        assert result_dict["message"] == "操作成功"
        assert result_dict["data"]["order_id"] == "123"
        assert "timestamp" in result_dict

    def test_result_fail_to_dict(self):
        """测试失败结果转换为字典"""
        result = Result.fail(error_code="ORDER_FAILED", message="订单失败")
        result_dict = result.to_dict()

        assert result_dict["code"] == "error"
        assert result_dict["error_code"] == "ORDER_FAILED"
        assert result_dict["message"] == "订单失败"

    def test_shortcut_functions(self):
        """测试快捷函数"""
        result1 = ok(data={"test": "data"})
        assert result1.is_success

        result2 = fail(error_code="ERROR", message="错误")
        assert result2.is_error

        result3 = warning(message="警告")
        assert result3.is_warning


class TestResultWithFixtures:
    """使用夹具测试 Result"""

    def test_with_mock_success(self, mock_result_success):
        """测试模拟成功结果"""
        assert mock_result_success.is_success
        assert mock_result_success.data["order_id"] == "123"

    def test_with_mock_error(self, mock_result_error):
        """测试模拟失败结果"""
        assert mock_result_error.is_error
        assert mock_result_error.error_code == "TEST_ERROR"
