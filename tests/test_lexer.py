from watchadoin.lexer import TaskPaperLexer, Token


def test_token_empty():
    tok = Token()
    assert tok.type == None
    assert tok.value == None
    assert tok.lineno == 1
    assert tok.index == 0
    assert repr(tok) == "Token(None, None, 1, 0)"


def test_token_all_attrib():
    tok = Token(type="TOKEN", value="abc", lineno=2, index=4)
    assert tok.type == "TOKEN"
    assert tok.value == "abc"
    assert tok.lineno == 2
    assert tok.index == 4
    assert repr(tok) == "Token('TOKEN', 'abc', 2, 4)"


def test_lexer_empty_document():
    lexer = TaskPaperLexer()
    tokens = list(lexer.tokenize_text("", eof=False))
    assert tokens == []
