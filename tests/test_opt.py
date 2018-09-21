import pytest
import sys
from loguru import logger
import ansimarkup

def test_record(writer):
    logger.start(writer, format="{message}")

    logger.opt(record=True).debug("1")
    logger.opt(record=True).debug("2 {record[level]}")
    logger.opt(record=True).log(11, "3 {0} {a} {record[level].no}", 4, a=5)

    assert writer.read() == '1\n2 DEBUG\n3 4 5 11\n'

def test_exception_boolean(writer):
    logger.start(writer, format="{level.name}: {message}")

    try:
        1 / 0
    except:
        logger.opt(exception=True).debug("Error {0} {record}", 1, record="test")

    lines = writer.read().strip().splitlines()

    assert lines[0] == "DEBUG: Error 1 test"
    assert lines[-1] == "ZeroDivisionError: division by zero"

def test_exception_exc_info(writer):
    logger.start(writer, format="{message}")

    try:
        1 / 0
    except:
        exc_info = sys.exc_info()

    logger.opt(exception=exc_info).debug("test")

    lines = writer.read().strip().splitlines()

    assert lines[0] == "test"
    assert lines[-1] == "ZeroDivisionError: division by zero"

def test_exception_class(writer):
    logger.start(writer, format="{message}")

    try:
        1 / 0
    except:
        _, exc_class, _ = sys.exc_info()

    logger.opt(exception=exc_class).debug("test")

    lines = writer.read().strip().splitlines()

    assert lines[0] == "test"
    assert lines[-1] == "ZeroDivisionError: division by zero"

def test_lazy(writer):
    counter = 0
    def laziness():
        nonlocal counter
        counter += 1
        return counter

    logger.start(writer, level=10, format="{level.no} => {message}")

    logger.opt(lazy=True).log(10, "1: {lazy}", lazy=laziness)
    logger.opt(lazy=True).log(5, "2: {0}", laziness)

    logger.stop()

    logger.opt(lazy=True).log(20, "3: {}", laziness)

    a = logger.start(writer, level=15, format="{level.no} => {message}")
    b = logger.start(writer, level=20, format="{level.no} => {message}")

    logger.log(17, "4: {}", counter)
    logger.opt(lazy=True).log(14, "5: {lazy}", lazy=lambda: counter)

    logger.stop(a)

    logger.opt(lazy=True).log(16, "6: {0}", lambda: counter)

    logger.opt(lazy=True).info("7: {}", laziness)
    logger.debug("7: {}", counter)

    assert writer.read() == "10 => 1: 1\n17 => 4: 1\n20 => 7: 2\n"

def test_depth(writer):
    logger.start(writer, format="{function} : {message}")

    def a():
        logger.opt(depth=0).debug("Test 1")
        logger.opt(depth=1).debug("Test 2")

    a()

    logger.stop()

    assert writer.read() == "a : Test 1\ntest_depth : Test 2\n"

def test_ansi(writer):
    logger.start(writer, format="<red>a</red> {message}", colorize=True)
    logger.opt(ansi=True).debug("<blue>b</blue>")
    assert writer.read() == ansimarkup.parse("<red>a</red> <blue>b</blue>\n")

def test_ansi_not_colorize(writer):
    logger.start(writer, format="<red>a</red> {message}", colorize=False)
    logger.opt(ansi=True).debug("<blue>b</blue>")
    assert writer.read() == ansimarkup.strip("<red>a</red> <blue>b</blue>\n")

def test_ansi_dont_color_unrelated(writer):
    logger.start(writer, format="{message} {extra[trap]}", colorize=True)
    logger.bind(trap="<red>B</red>").opt(ansi=True).debug("<red>A</red>")
    assert writer.read() == ansimarkup.parse("<red>A</red>") + " <red>B</red>\n"

def test_ansi_with_record(writer):
    logger.start(writer, format="{message}", colorize=True)
    logger_ = logger.bind(start="<red>", end="</red>")
    logger_.opt(ansi=True, record=True).debug("{record[extra][start]}B{record[extra][end]}")
    assert writer.read() == ansimarkup.parse("<red>B</red>\n")

@pytest.mark.xfail
def test_ansi_nested(writer):
    logger.start(writer, format="(<red>[{message}]</red>)", colorize=True)
    logger.opt(ansi=True).debug("A <green>B</green> C <blue>D</blue> E")
    assert writer.read() == ansimarkup.parse("(<red>[A<green>B</green>C<blue>D</blue>E]</red>)\n")

def test_ansi_raising(writer):
    logger.start(writer, format="<red>{message}</red>", colorize=True, catch=False)
    with pytest.raises(ansimarkup.markup.MismatchedTag):
        logger.opt(ansi=True).debug("X </red> <red> Y")

def test_ansi_with_args(writer):
    logger.start(writer, format="=> {message} <=", colorize=True)
    logger.opt(ansi=True).debug("the {0}test{end}", "<red>", end="</red>")
    assert writer.read() == ansimarkup.parse("=> the <red>test</red> <=") + '\n'

def test_ansi_with_level(writer):
    logger.start(writer, format="{message}", colorize=True)
    logger.level("DEBUG", color="<green>")
    logger.opt(ansi=True).debug("a <level>level</level> b")
    assert writer.read() == ansimarkup.parse("a <green>level</green> b")+ '\n'

def test_raw(writer):
    logger.start(writer, format="", colorize=True)
    logger.opt(raw=True).info("Raw {}", "message")
    assert writer.read() == "Raw message"

def test_raw_with_format_function(writer):
    logger.start(writer, format=lambda _: "{time} \n")
    logger.opt(raw=True).debug("Raw {message} bis", message="message")
    assert writer.read() == "Raw message bis"

def test_raw_with_ansi(writer):
    logger.start(writer, format="XYZ", colorize=True)
    logger.opt(raw=True, ansi=True).info("Raw <red>colors</red> and <lvl>level</lvl>")
    assert writer.read() == ansimarkup.parse("Raw <red>colors</red> and <b>level</b>")

def test_raw_with_record(writer):
    logger.start(writer, format="Nope\n")
    logger.opt(raw=True, record=True).debug("Raw in '{record[function]}'\n")
    assert writer.read() == "Raw in 'test_raw_with_record'\n"

def test_keep_extra(writer):
    logger.configure(extra=dict(test=123))
    logger.start(writer, format='{extra[test]}')
    logger.opt().debug("")

    assert writer.read() == "123\n"

def test_before_bind(writer):
    logger.start(writer, format='{message}')
    logger.opt(record=True).bind(key="value").info("{record[level]}")
    assert writer.read() == "INFO\n"
