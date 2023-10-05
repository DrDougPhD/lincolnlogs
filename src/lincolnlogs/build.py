import datetime
import logging
from logging.handlers import TimedRotatingFileHandler
import os
import pathlib

from . import notebook
from . import monkeypatch

default_level = logging.getLevelName(logging.INFO)


def it(verbosity: str = default_level) -> logging.Logger:
    # Grab the root logger
    logger = logging.getLogger()

    level = logging.getLevelName(verbosity)
    logger.setLevel(level)

    if len(logger.handlers) > 0:
        # Setup likely called multiple times
        # Override the previous handlers' levels to match the new level
        for handler in logger.handlers:
            handler.setLevel(level)

        return logger

    command_line_handler = logging.StreamHandler()
    command_line_handler.setLevel(level)

    if level == logging.DEBUG:
        debug_logger(logger, command_line_handler)

    else:
        logger.addHandler(command_line_handler)

    monkeypatch.apply()

    return logger


def debug_logger(logger: logging.Logger, command_line_handler):
    """Setup a logger that uses special logging to file and with line numbers and module paths."""

    project_root = pathlib.Path.cwd()
    logging_directory = project_root / 'logs'
    logging_directory.mkdir(parents=True, exist_ok=True)
 
    # filename_timestamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    file_log_handler = TimedRotatingFileHandler(
        filename=logging_directory / 'debug.log',
        when='midnight',
        backupCount=5,
    )
    file_log_handler.setLevel(logging.DEBUG)
 
    default_record_factory = logging.getLogRecordFactory()
    def relative_pathname_record_factory(*args, **kwargs):
        record = default_record_factory(*args, **kwargs)
        record_path = pathlib.Path(record.pathname)
 
        try:
            record_source_file_relative_path = record_path.relative_to(project_root)
 
        except ValueError:
            if notebook.called_me():
                # Jupyter notebooks currently break functionality, so let's not worry about relative paths
                record.relpathname = 'Notebook'
                return record
           
            else:
                # Calling code block likely in a virtual environment
                record_source_file_relative_path = pathlib.Path(
                    str(record_path).split(f'site-packages{os.sep}')[-1]
                )
       
        if record_source_file_relative_path.name == '__init__.py':
            record_source_file_relative_path = record_source_file_relative_path.parent
       
        module_path = str(record_source_file_relative_path).replace(os.sep, '.')
 
        # Remove `.py` extension
        if module_path.endswith('.py'):
            module_path = module_path[:-3]
 
        record.relpathname = module_path
        return record
    logging.setLogRecordFactory(relative_pathname_record_factory)
 
    try:
        import colorlog
        # add colors to the logs
        source_files_funcs_linenos_formatter = colorlog.ColoredFormatter(
            fmt=(
                '%(asctime)s - %(log_color)s%(levelname)-8s%(reset)s'
                ' [ %(relpathname)s::%(funcName)s():%(lineno)s ] '
                '%(message)s'
            ),
            datefmt='%Y-%m-%d %H:%M:%S',
            reset=True,
        )

    except ImportError:
        # `colorlog` is not installed, so don't use it
        source_files_funcs_linenos_formatter = logging.Formatter(
            fmt=(
                '%(asctime)s - s%(levelname)-8s'
                ' [ %(relpathname)s::%(funcName)s():%(lineno)s ] '
                '%(message)s'
            ),
            datefmt='%Y-%m-%d %H:%M:%S',
        )
 
    for handler in (file_log_handler, command_line_handler):
        handler.setFormatter(source_files_funcs_linenos_formatter)
        logger.addHandler(handler)
   
    return logger
