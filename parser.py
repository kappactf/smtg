from html.parser import HTMLParser

class TelegramHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.output = ""
        self.visible = True
    
    def handle_starttag(self, tag, attrs):
        if tag == "br":
            self.output += "\n"
        elif tag == "code":
            self.output += "<code>"
        elif tag in ["b", "strong"]:
            self.output += "<b>"
        elif tag in ["i", "em"]:
            self.output += "<i>"
        elif tag == "a":
            url = ""
            for attr in attrs:
                if attr[0] == "href":
                    url = attr[1]
                    break
            self.output += f"<a href=\"{url}\">"
        elif tag in ["script", "style"]:
            self.visible = False

    def handle_endtag(self, tag):
        if tag == "p":
            self.output += "\n\n"
        elif tag == "code":
            self.output += "</code>"
        elif tag in ["b", "strong"]:
            self.output += "</b>"
        elif tag in ["i", "em"]:
            self.output += "</i>"
        elif tag == "a":
            self.output += "</a>"
        elif tag in ["script", "style"]:
            self.visible = True

    def handle_data(self, data):
        if self.visible:
            self.output += data

