import html
import re
from html.parser import HTMLParser


class HTMLSplitter(HTMLParser):
    """Splits HTML message to several messages not longer than 4KB."""

    def __init__(self):
        super().__init__()
        self.active_part = ""
        self.parts = []
        self.tag_stack = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()

        self.push_starttag(tag, attrs)
        self.tag_stack.append((tag, attrs))

    
    def handle_data(self, data: str) -> None:
        data = html.escape(data, False)

        if len(self.active_part) + len(data) >= 3876:
            data_size = max(3939 - len(self.active_part), 0)

            self.active_part += data[:data_size]
            for item in self.tag_stack[::-1]:
                self.push_endtag(item[0])
            self.parts.append(self.active_part)
            self.active_part = ""
            for item in self.tag_stack:
                self.push_starttag(*item)
            self.handle_data(data[data_size:])
        else:
            self.active_part += data

    def handle_endtag(self, tag: str) -> None:
        self.push_endtag(tag)
        self.tag_stack.pop()
    
    def push_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.active_part += f"<{tag}"
        for attr in attrs:
            name, value = attr
            self.active_part += f" {name}=\"{html.escape(value or '')}\""
        self.active_part += ">"

    def push_endtag(self, tag: str) -> None:
        self.active_part += f"</{tag}>"
    
    def close(self) -> None:
        self.parts.append(self.active_part)

        super().close()


class HTMLSimplifier(HTMLParser):
    """Converts rich HTML message to Telegram HTML."""

    def __init__(self):
        super().__init__()
        self.result = ""
        self.is_visible = True
        self.tag_stack = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if not self.is_visible:
            return

        tag = tag.lower()

        match tag:
            case "br":
                self.result += "\n"
            case "code":
                self.result += "<code>"
            case "b" | "strong":
                self.result += "<b>"
            case "i" | "em":
                self.result += "<i>"
            case "a":
                url = "#"
                for attr in attrs:
                    name, value = attr
                    if name.lower() == "href" and value is not None:
                        url = value
                        break
                self.result += f"<a href=\"{html.escape(url)}\">"
            case "script" | "style":
                self.is_visible = False
        
        if tag in ["code", "b", "strong", "i", "em", "a"]:
            self.tag_stack.append(tag)
    
    def handle_data(self, data: str) -> None:
        if not self.is_visible:
            return

        data = re.sub(r"\s+", " ", data)
        if len(data.strip()) > 0:
            self.result += html.escape(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in ["script", "style"]:
            self.is_visible = True
        if not self.is_visible:
            return
        
        if tag in ["code", "b", "strong", "i", "em", "a"]:
            if tag in self.tag_stack:
                while tag != self.tag_stack[-1]:
                    self.close_tag(self.tag_stack[-1])
                    self.tag_stack.pop()
                self.close_tag(tag)
                self.tag_stack.pop()
        else:
            self.close_tag(tag)
                

    def close_tag(self, tag: str) -> None:
        match tag:
            case "p" | "div":
                self.result += "\n\n"
            case "code":
                self.result += "</code>"
            case "b" | "strong":
                self.result += "</b>"
            case "i" | "em":
                self.result += "</i>"
            case "a":
                self.result += "</a>"
    
    def close(self) -> None:
        super().close()

        while len(self.tag_stack) > 0:
            self.close_tag(self.tag_stack[-1])
            self.tag_stack.pop()

        self.result = re.sub(r"\n{3,}", "\n\n", self.result)
