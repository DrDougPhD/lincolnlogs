import logging
import os
import pathlib
import random
import re
import inspect
from typing import Collection

import pytest

import lincolnlogs


def get_log_record(log_message, records: Collection[logging.LogRecord]) -> logging.LogRecord:
    return next(filter(
        lambda r: log_message == r.msg,
        records,
    ))


def format_log_record(handler: logging.Handler, record: logging.LogRecord) -> str:
    return handler.format(record)


@pytest.fixture(autouse=True)
def debug_logger() -> logging.Logger:
    return lincolnlogs.setup(verbosity='DEBUG')


@pytest.fixture
def sample_log_message() -> str:
    return f'Test Log {random.randint(0, 100)}'


@pytest.fixture
def sample_log_record(debug_logger, sample_log_message, caplog) -> logging.LogRecord:
    debug_logger.debug(sample_log_message)
    return get_log_record(log_message=sample_log_message, records=caplog.records)


@pytest.fixture
def file_handler(debug_logger) -> logging.FileHandler:
    return next(filter(
        lambda h: type(h) is logging.FileHandler,
        debug_logger.handlers,
    ))


@pytest.fixture
def formatted_message(file_handler, sample_log_record) -> str:
    return format_log_record(handler=file_handler, record=sample_log_record)


def test_debug_level_has_file_handler(debug_logger):
    for handler in debug_logger.handlers:
        if type(handler) is logging.FileHandler:
            return
    
    pytest.fail('No `logging.FileHandler` instances on logger')


def test_debug_level_produces_file(file_handler):
    actual_log_file = pathlib.Path(file_handler.baseFilename)
    assert actual_log_file.exists(), (
        f'Log file at `{actual_log_file}` could not be found'
    )


def test_debug_level_has_timestamp_in_message(formatted_message):
    timestamp_pattern = re.compile('\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}')
    assert timestamp_pattern.match(formatted_message), (
        f'No timestamp was found in log message `{formatted_message}`'
    )


def test_debug_level_has_level_name_in_message(formatted_message):
    assert 'DEBUG' in formatted_message, (
        f'Log level `DEBUG` was not found in log message `{formatted_message}`'
    )


def test_debug_level_has_source_relative_path_in_message(sample_log_record, formatted_message):
    relative_source_path = pathlib.Path(__file__).relative_to(pathlib.Path.cwd())
    relative_source_module = str(relative_source_path)\
        .replace(os.sep, '.')\
        .removesuffix('.py')

    source_path_segment_regex = re.compile('\[ (?P<source_path_segment>.+)::.+\(\):\d+ \]')
    actual_source_path = source_path_segment_regex.search(formatted_message)\
        .groupdict()\
        .get('source_path_segment')

    assert actual_source_path == relative_source_module, (
        'Unexpected source path in log'
    )


def test_debug_level_has_source_function_name_in_message(debug_logger, sample_log_message, caplog):
    debug_logger.debug(sample_log_message)

    expected_calling_function_name = inspect.currentframe().f_code.co_name
    
    log_record = get_log_record(log_message=sample_log_message, records=caplog.records)
    actual_message = format_log_record(
        handler=debug_logger.handlers[0],
        record=log_record
    )

    function_segment_regex = re.compile('\[ (?P<source_path_segment>.+)::(?P<function_name>.+)\(\):\d+ \]')
    actual_function_name = function_segment_regex.search(actual_message)\
        .groupdict()\
        .get('function_name')

    assert actual_function_name == expected_calling_function_name, (
        'Unexpected calling function in formatted log record'
    )


def test_debug_level_has_code_line_number_in_message(sample_log_record, debug_logger):
    actual_message = format_log_record(
        handler=debug_logger.handlers[0],
        record=sample_log_record
    )

    function_segment_regex = re.compile('\[ (?P<source_path_segment>.+)::(?P<function_name>.+)\(\):(?P<source_line_number>\d+) \]')
    pattern_match = function_segment_regex.search(actual_message)
    
    assert pattern_match is not None, (
        'No proper line number found in log message'
    )
    assert int(pattern_match.groupdict().get('source_line_number')) > 0, (
        'Line number in log message is negative'
    )


def test_debug_level_has_message(sample_log_message, formatted_message):
    assert sample_log_message in formatted_message, (
        'Log does not contain the expected message'
    )
