"""
Drill XML
https://github.com/dcwatson/drill
"""

__version_info__ = (1, 0, 0)
__version__ = '.'.join(str(i) for i in __version_info__)

from xml.sax import make_parser
from xml.sax.handler import feature_namespaces, ContentHandler
from xml.sax.saxutils import escape, quoteattr
from xml.sax.xmlreader import InputSource
import sys

PY3 = sys.version_info[0] == 3

if PY3:
    from io import StringIO as string_io
    from io import BytesIO as bytes_io
    import urllib.request as url_lib
    unicode = str
    basestring = str
    xrange = range
else:
    from StringIO import StringIO as string_io
    from cStringIO import StringIO as bytes_io
    import urllib2 as url_lib

class XmlWriter (object):
    """
    A class for safely writing XML to a stream, with optional pretty-printing and replacements.
    """

    def __init__(self, stream, encoding='utf-8', pretty=True, indent='    ', level=0, invalid='', replacements=None):
        self.stream = stream
        self.encoding = encoding
        self.pretty = pretty
        self.level = level
        self.replacements = {}
        for c in range(32):
            # \t, \n, and \r are the only valid control characters in XML.
            if c not in (9, 10, 13):
                self.replacements[chr(c)] = invalid
        if replacements:
            self.replacements.update(replacements)
        self.indent = escape(indent, self.replacements)

    def _write(self, data):
        self.stream.write(data.encode(self.encoding))

    def data(self, data, newline=False):
        self._write(escape(unicode(data).strip(), self.replacements))
        if self.pretty and newline:
            self._write('\n')

    def start(self, tag, attrs, newline=False):
        if self.pretty:
            self._write(self.indent * self.level)
        self._write('<')
        self._write(escape(tag, self.replacements))
        for attr, value in attrs.items():
            if value is None:
                value = ''
            self._write(' ')
            self._write(escape(unicode(attr), self.replacements))
            self._write('=')
            self._write(quoteattr(unicode(value), self.replacements))
        self._write('>')
        if self.pretty and newline:
            self._write('\n')
        self.level += 1

    def end(self, tag, indent=False, newline=True):
        self.level -= 1
        if self.pretty and indent:
            self._write(self.indent * self.level)
        self._write('</')
        self._write(escape(tag, self.replacements))
        self._write('>')
        if self.pretty and newline:
            self._write('\n')

    def simple_tag(self, tag, attrs={}, data=None):
        self.start(tag, attrs, newline=False)
        if data is not None:
            self.data(data, newline=False)
        self.end(tag, indent=False)

class XmlElement (object):
    """
    A mutable object encapsulating an XML element.
    """

    def __init__(self, name, attrs=None, data=None, parent=None, index=None):
        self.tagname = name
        self.parent = parent
        self.index = index # The index of this node in the parent's children list.
        self.attrs = {}
        if attrs:
            self.attrs.update(attrs)
        self.data = ''
        if data:
            self.data += unicode(data)
        self._children = []

    def __repr__(self):
        return '<XmlElement %s>' % self.tagname

    def __unicode__(self):
        return self.data

    def __str__(self):
        if PY3:
            return self.data
        else:
            return self.data.encode('utf-8')

    def __bool__(self):
        """
        If we exist, we should evaluate to True, even if __len__ returns 0.
        """
        return True
    __nonzero__ = __bool__

    def __len__(self):
        """
        Return the number of child nodes.
        """
        return len(self._children)

    def __getitem__(self, idx):
        """
        Returns the child node at the given index.
        """
        if isinstance(idx, basestring):
            return self.attrs.get(idx)
        return self._children[idx]

    def __getattr__(self, name):
        """
        Allows access to any attribute or child node directly.
        """
        return self.first(name)

    def _characters(self, ch=None):
        """
        Called when the parser detects character data while in this node.
        """
        if ch is not None:
            self.data += unicode(ch)

    def _finalize(self):
        """
        Called when the parser detects an end tag.
        """
        self.data = self.data.strip()

    def write(self, writer):
        """
        Writes an XML representation of this node (including descendants) to the specified file-like object.
        """
        multiline = bool(self._children)
        newline_start = multiline and not bool(self.data)
        writer.start(self.tagname, self.attrs, newline=newline_start)
        if self.data:
            writer.data(self.data, newline=bool(self._children))
        for c in self._children:
            c.write(writer)
        writer.end(self.tagname, indent=multiline)

    def xml(self, **kwargs):
        """
        Returns an XML representation of this node (including descendants).
        """
        s = bytes_io()
        writer = XmlWriter(s, **kwargs)
        self.write(writer)
        return s.getvalue()

    def append(self, name, attrs=None, data=None):
        """
        Called when the parser detects a start tag (child element) while in this node.
        """
        elem = XmlElement(name, attrs, data, self, len(self._children))
        self._children.append(elem)
        return elem

    def insert(self, before, name, attrs=None, data=None):
        """
        Inserts a new element as a child of this element, before the specified index or sibling.
        """
        if isinstance(before, XmlElement):
            if before.parent != self:
                raise ValueError('Cannot insert before an XmlElement with a different parent.')
            before = before.index
        # Make sure 0 <= before <= len(_children).
        before = min(max(0, before), len(self._children))
        elem = XmlElement(name, attrs, data, self, before)
        self._children.insert(before, elem)
        # Re-index all the children.
        for idx, c in enumerate(self._children):
            c.index = idx
        return elem

    def clear(self):
        """
        Clears out all children, attributes, and data.
        """
        self.attrs = {}
        self.data = ''
        self._children = []

    def items(self):
        """
        A Generator yielding ``key: value`` attribute pairs, sorted by key name.
        """
        for key in sorted(self.attrs):
            yield key, self.attrs[key]

    def children(self, name=None, reverse=False):
        """
        A generator yielding children of this node.

        :param name: If specified, only consider elements with this tag name
        :param reverse: If ``True``, children will be yielded in reverse declaration order
        """
        elems = self._children
        if reverse:
            elems = reversed(elems)
        for elem in elems:
            if name is None or elem.tagname == name:
                yield elem

    def find(self, name=None):
        """
        Recursively find any descendants of this node with the given tag name. If a tag name
        is omitted, this will yield every descendant node.

        :param name: If specified, only consider elements with this tag name
        :returns: A generator yielding descendants of this node
        """
        for c in self._children:
            if name is None or c.tagname == name:
                yield c
            for gc in c.find(name):
                yield gc

    def first(self, name=None):
        """
        Returns the first child of this node.

        :param name: If specified, only consider elements with this tag name
        :rtype: :class:`XmlElement`
        """
        for c in self.children(name):
            return c

    def last(self, name=None):
        """
        Returns the last child of this node.

        :param name: If specified, only consider elements with this tag name
        :rtype: :class:`XmlElement`
        """
        for c in self.children(name, reverse=True):
            return c

    def next(self, name=None):
        """
        Returns the next sibling of this node.

        :param name: If specified, only consider elements with this tag name
        :rtype: :class:`XmlElement`
        """
        if self.parent is None or self.index is None:
            return None
        for idx in xrange(self.index + 1, len(self.parent)):
            if name is None or self.parent[idx].tagname == name:
                return self.parent[idx]

    def prev(self, name=None):
        """
        Returns the previous sibling of this node.

        :param name: If specified, only consider elements with this tag name
        :rtype: :class:`XmlElement`
        """
        if self.parent is None or self.index is None:
            return None
        for idx in xrange(self.index - 1, -1, -1):
            if name is None or self.parent[idx].tagname == name:
                return self.parent[idx]

class DrillContentHandler (ContentHandler):

    def __init__(self, queue=None):
        self.root = None
        self.current = None
        self.queue = queue

    def startElement(self, name, attrs):
        if not self.root:
            self.root = XmlElement(name, attrs)
            self.current = self.root
        elif self.current is not None:
            self.current = self.current.append(name, attrs)

    def endElement(self, name):
        if self.current is not None:
            self.current._finalize()
            if self.queue:
                self.queue.add(self.current)
            self.current = self.current.parent

    def characters(self, ch):
        if self.current is not None:
            self.current._characters(ch)

def parse(url_or_path, encoding=None):
    """
    :param url_or_path: A file-like object, a filesystem path, a URL, or a string containing XML
    :rtype: :class:`XmlElement`
    """
    handler = DrillContentHandler()
    parser = make_parser()
    parser.setFeature(feature_namespaces, 0)
    parser.setContentHandler(handler)
    if isinstance(url_or_path, basestring):
        if '://' in url_or_path[:20]:
            # A URL.
            parser.parse(url_lib.urlopen(url_or_path))
        elif url_or_path[:100].strip().startswith('<'):
            # Actual XML data.
            if isinstance(url_or_path, unicode):
                # The parser doesn't like unicode strings, encode it to UTF-8 (or whatever) bytes.
                if encoding is None:
                    encoding = 'utf-8'
                url_or_path = url_or_path.encode(encoding)
            src = InputSource()
            src.setByteStream(bytes_io(url_or_path))
            if encoding:
                src.setEncoding(encoding)
            parser.parse(src)
        else:
            # Assume a filesystem path.
            parser.parse(open(url_or_path, 'rb'))
    elif PY3 and isinstance(url_or_path, bytes):
        # For Python 3 bytes, create an InputSource and set the byte stream.
        src = InputSource()
        src.setByteStream(bytes_io(url_or_path))
        if encoding:
            src.setEncoding(encoding)
        parser.parse(src)
    else:
        # A file-like object or an InputSource.
        parser.parse(url_or_path)
    return handler.root

class DrillElementIterator (object):
    READ_CHUNK_SIZE = 16384

    def __init__(self, filelike, parser):
        self.filelike = filelike
        self.parser = parser
        self.elements = []

    def add(self, element):
        self.elements.append(element)

    def __next__(self):
        return self.next()

    def next(self):
        while not self.elements:
            data = self.filelike.read(self.READ_CHUNK_SIZE)
            if not data:
                raise StopIteration
            # Feeding the parser will cause the handler to call our add method for parsed elements.
            self.parser.feed(data)
        return self.elements.pop(0)

    def __iter__(self):
        return self

def iterparse(filelike):
    """
    :param filelike: A file-like object with a ``read`` method
    :returns: An iterator returning :class:`XmlElement`
    """
    parser = make_parser(['xml.sax.expatreader'])
    parser.setFeature(feature_namespaces, 0)
    elem_iter = DrillElementIterator(filelike, parser)
    handler = DrillContentHandler(elem_iter)
    parser.setContentHandler(handler)
    return elem_iter
