"""
20 Unit Tests for normalize_year() function (Day 41).
Covers all format variants and edge cases.
"""

import pytest
from src.etl.normalizer import normalize_year


def test_year_standard_int():
    assert normalize_year(2024) == 2024


def test_year_standard_float():
    assert normalize_year(2021.0) == 2021


def test_year_four_digit_string():
    assert normalize_year("2023") == 2023


def test_year_month_year_mar_2014():
    assert normalize_year("Mar 2014") == 2014


def test_year_month_year_dec_2012():
    assert normalize_year("Dec 2012") == 2012


def test_year_month_hyphen_two_digit():
    assert normalize_year("Mar-13") == 2013


def test_year_month_slash_two_digit():
    assert normalize_year("Mar/18") == 2018


def test_year_with_suffix_9m():
    assert normalize_year("Mar 2016 9m") == 2016


def test_year_with_suffix_number():
    assert normalize_year("Mar 2023 15") == 2023


def test_year_fy_prefix():
    assert normalize_year("FY22") == 2022


def test_year_fy_full():
    assert normalize_year("FY 2020") == 2020


def test_year_jan_month():
    assert normalize_year("Jan 2019") == 2019


def test_year_sep_month():
    assert normalize_year("Sep 2017") == 2017


def test_year_ttm_returns_none():
    assert normalize_year("TTM") is None


def test_year_ttm_lowercase_returns_none():
    assert normalize_year("ttm") is None


def test_year_none_returns_none():
    assert normalize_year(None) is None


def test_year_empty_string_returns_none():
    assert normalize_year("") == None


def test_year_unknown_returns_none():
    assert normalize_year("Unknown") is None


def test_year_nan_string_returns_none():
    assert normalize_year("NaN") is None


def test_year_whitespace_around_value():
    assert normalize_year("   2024   ") == 2024
