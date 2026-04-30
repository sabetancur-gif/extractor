import pytest
from src.translation.translator import Translator


def test_mock_translation_basic():
    translator = Translator(backend="mock")
    text = "Hello world"
    out = translator.translate(text, target_lang="es")

    assert out == "[es] Hello world"


def test_mock_translation_empty_text():
    translator = Translator(backend="mock")
    out = translator.translate("", target_lang="en")

    assert out == "[en] "


def test_unknown_backend_raises_error():
    translator = Translator(backend="unknown")

    with pytest.raises(NotImplementedError):
        translator.translate("Hello", "es")


def test_openai_backend_not_implemented():
    translator = Translator(backend="openai")

    with pytest.raises(NotImplementedError):
        translator.translate("Hello", "es")