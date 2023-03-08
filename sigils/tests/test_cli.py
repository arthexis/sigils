import subprocess as sp


# Test calling from the command line
def test_cli_error_missing_context():
    result = sp.run(["sigils", "Hello [[WORLD]]", "-e", ""], capture_output=True)
    assert result.stdout == b""
    assert result.stderr != b""


# Test calling from the command line with a custom function
def test_cli_custom_function():
    result = sp.run(
        ["sigils", "[[SYS.ENV.PATH]]", "--on-error", "ignore"], 
        capture_output=True)
    assert result.stdout not in (b"", b"None", b"[[SYS.ENV.PATH]]")
    assert result.stderr == b""
