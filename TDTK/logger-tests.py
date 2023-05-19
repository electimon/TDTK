from TDTK.logger import log

# Tests that the function logs a message with no type specified.  
class Tests:
    def test_log_no_type(self, capsys):
        message = "This is a test message"
        log(message)
        # Assert that the message was printed with no type and no indentation
        assert f"{message}\n" == capsys.readouterr().out

    def test_log_valid_type(self, capsys):
        message = "This is a test message"
        log(message, type="result")
        # Assert that the message was printed with the correct type and indentation
        assert f"  - {message}\n" in capsys.readouterr().out

    def test_log_invalid_type(self, capsys):
        message = "This is a test message"
        log(message, type="invalid")
        # Assert that the message was printed with no type and no indentation
        assert f"{message}\n" == capsys.readouterr().out

    def test_log_non_string_type(self, capsys):
        message = "This is a test message"
        log(message, type=str(123))
        # Assert that the message was printed with no type and no indentation
        assert f"{message}\n" == capsys.readouterr().out

    def test_log_large_message(self, capsys):
        message = "a" * 1000
        log(message, type="result")
        # Assert that the message was printed with the correct type and indentation
        assert f"  - {message}\n" in capsys.readouterr().out

    def test_log_empty_string_type(self, capsys):
        message = "This is a test message"
        log(message, type="")
        # Assert that the message was printed with no type and no indentation
        assert f"{message}\n" == capsys.readouterr().out

