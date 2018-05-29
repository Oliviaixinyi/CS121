import re
from collections import defaultdict, Generator

from bs4 import BeautifulSoup, Comment


class Html:
    """
    This class is a Parser to parse HTML files, a path like "0/0" and a url like "https://..."
    will be required as parameters in __init__ method
    """

    def __init__(self, path, url):

        """
        Type of file can be parsed by Html
        html        pass
        txt         pass
        makefile    pass

        jpg         no pass
        """

        self.path = path
        self.url = url

        self.data = ''.join(open("./WEBPAGES_RAW/" + path, encoding="utf-8").readlines()).lower()

        try:
            self._is_html = True
            self.soup = BeautifulSoup(self.data, 'html.parser')
        except:
            self._is_html = False
            print('not html')

    def token_metas(self) -> Generator:
        """
        This method will filter out unrelated data in a html file and return a Counter
        of the tokens and the occurrence of tokens in the html file
        """
        positions = defaultdict(list)
        weights = defaultdict(int)

        if self._is_html:

            self.parse_title(weights)
            self.parse_headers(weights)

            for comment in self.soup.findAll(text=lambda text: isinstance(text, Comment)):
                comment.extract()

            # strip off the content surrounded by <script>
            for script in self.soup('script'):
                script.extract()

            # strip off the content surrounded by <link>
            for link in self.soup('link'):
                link.extract()

            # strip off the CSS style, which is surrounded by <style>
            for style in self.soup("style"):
                style.extract()

            # find all text nodes and choose the ones that is a word
            tokens = self.soup.get_text(separator=" ", strip=True)
            tokens = re.findall("[\w']+", tokens)

            for i, token in enumerate(tokens):
                positions[token].append(i)
                self._increment_token_weight(weights, token=token)

            for token in set(tokens):
                yield (token, {'weight': weights[token], 'all-positions': positions[token]})

    def parse_title(self, _weight_dict: dict):
        self._increment_token_weight(_weight_dict, tag="title", weight=4)

    def parse_headers(self, _weight_dict: dict):
        for tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            self._increment_token_weight(_weight_dict, tag=tag, weight=2)

    def _increment_token_weight(self, _weight_dict: dict, token=None, tag=None, weight=1):
        if tag:
            for node in self.soup.find_all(tag):
                for token in re.findall("[a-zA-Z\d]+", node.get_text()):
                    _weight_dict[token] += weight
        elif token:
            _weight_dict[token] += weight
        else:
            raise RuntimeError("no token or tag specified")
