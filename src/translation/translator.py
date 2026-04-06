# src/translation/translator.py
class Translator:
    def __init__(self, backend="mock", config=None):
        self.backend = backend
        self.config = config or {}

    def translate(self, text: str, target_lang: str) -> str:
        if self.backend == "mock":
            return f"[{target_lang}] {text}"
        if self.backend == "openai":
            # implement adapter calling OpenAI API (not included here)
            raise NotImplementedError
        # add other backends
        raise NotImplementedError