"""This."""
# src/conversion/formatter.py
import markdown as md_lib


class Converter:
    """This."""
    def __init__(self):
        """This."""
        pass

    def to_markdown(self, document_json: dict) -> str:
        """This."""
        lines = []
        for p in document_json.get("pages", []):
            for b in p.get("blocks", []):
                t = b.get("text", "").strip()
                if not t:
                    continue
                if b.get("type") == "title":
                    lines.append(f"# {t}")
                elif b.get("type") == "table":
                    lines.append(self._table_to_md(t))
                else:
                    lines.append(t + "\n")
            lines.append("\n---\n")
        return "\n".join(lines)

    def to_html(self, document_json: dict) -> str:
        """This."""
        md = self.to_markdown(document_json)
        return md_lib.markdown(md)

    def _table_to_md(self, text):
        # simple fallback: wrap as code block or implement parsing later
        return "\n" + text + "\n"
