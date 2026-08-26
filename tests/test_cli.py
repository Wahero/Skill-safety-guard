"""CLI 參數解析測試（P2-1）"""
import pytest

from skill_safety_guard.cli import parse_args


def test_default_target():
    """預設目標為當前目錄"""
    args = parse_args([])
    assert args.target == "."


def test_pi_flag():
    """--pi 旗標"""
    args = parse_args(["--pi"])
    assert args.pi is True


def test_output_json():
    """--output json"""
    args = parse_args(["--output", "json"])
    assert args.output == "json"


def test_version_exits():
    """--version 觸發 SystemExit（exit code 0）"""
    with pytest.raises(SystemExit) as exc_info:
        parse_args(["--version"])
    assert exc_info.value.code == 0


def test_report_fp():
    """--report-fp 設定"""
    args = parse_args(["--report-fp", "cred-openai"])
    assert args.report_fp == "cred-openai"
