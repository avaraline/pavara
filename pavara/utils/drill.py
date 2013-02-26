__version_info__ = (1, 1, 0)
__version__ = '.'.join(str(i) for i in __version_info__)

from xml.sax.saxutils import escape, quoteattr
from xml.parsers import expat
import contextlib
import sys
import re

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

xpath_re = re.compile(r'(?P<tag>[a-zA-Z0-9\.\*]+)(?P<predicate>\[.+\])?')
num_re = re.compile(r'[0-9\-]+')

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

def traverse(element, query, deep=False):
    """
    Helper function to traverse an element tree rooted at element, yielding nodes matching the query.
    """
    # Grab the next part of the query (it will be chopped from the front each iteration).
    part = query[0]
    if not part:
        # If the part is blank, we encountered a //, meaning search all sub-nodes.
        query = query[1:]
        part = query[0]
        deep = True
    # Parse out any predicate (tag[pred]) from this part of the query.
    part, predicate = xpath_re.match(query[0]).groups()
    for c in element._children:
        if part in ('*', c.tagname) and c._match(predicate):
            # A potential matching branch: this child matches the next query part (and predicate).
            if len(query) == 1:
                # If this is the last part of the query, we found a matching element, yield it.
                yield c
            else:
                # Otherwise, check the children of this child against the next query part.
                for e in traverse(c, query[1:]):
                    yield e
        if deep:
            # If we're searching all sub-nodes, traverse with the same query, regardless of matching.
            # This basically creates a recursion branch to search EVERYWHERE for anything after //.
            for e in traverse(c, query, deep=True):
                yield e

def parse_query(query):
    """
    Given a simplified XPath query string, returns an array of normalized query parts.
    """
    parts = query.split('/')
    norm = []
    for p in parts:
        p = p.strip()
        if p:
            norm.append(p)
        elif '' not in norm:
            norm.append('')
    return norm

class XmlQuery (object):
    """
    An iterable object returned by XmlElement.find, with convenience methods for getting the first and last elements
    of the result set.
    """

    def __init__(self, root, query):
        self.root = root
        self.query = query

    def __repr__(self):
        return '%s -> %s' % (self.root.path(), self.query)

    def __iter__(self):
        return traverse(self.root, parse_query(self.query))

    def first(self):
        """
        Returns the first matching element of this query, or None if there was no match.
        """
        for e in self:
            return e

    def last(self):
        """
        Returns the last matching element of this query, or None if there was no match.
        """
        last_found = None
        for e in self:
            last_found = e
        return last_found

class XmlElement (object):
    """
    A mutable object encapsulating an XML element.
    """

    # This makes a pretty big difference when parsing huge XML files.
    __slots__ = ('tagname', 'parent', 'index', 'attrs', 'data', '_children')

    def __init__(self, name, attrs=None, data=None, parent=None, index=None):
        self.tagname = name
        self.parent = parent
        self.index = index # The index of this node in the parent's children list.
        self.attrs = {}
        if attrs:
            self.attrs.update(attrs)
        self.data = unicode(data) if data else ''
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

    def write(self, writer):
        """
        Writes an XML representation of this node (including descendants) to the specified file-like object.

        :param writer: An :class:`XmlWriter` instance to write this node to
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
        Returns an XML representation of this node (including descendants). This method automatically creates an
        :class:`XmlWriter` instance internally to handle the writing.

        :param **kwargs: Any named arguments are passed along to the :class:`XmlWriter` constructor
        """
        s = bytes_io()
        writer = XmlWriter(s, **kwargs)
        self.write(writer)
        return s.getvalue()

    def append(self, name, attrs=None, data=None):
        """
        Called when the parser detects a start tag (child element) while in this node. Internally creates an
        :class:`XmlElement` and adds it to the end of this node's children.

        :param name: The tag name to add
        :param attrs: Attributes for the new tag
        :param data: CDATA for the new tag
        :returns: The newly-created element
        :rtype: :class:`XmlElement`
        """
        elem = XmlElement(name, attrs, data, self, len(self._children))
        self._children.append(elem)
        return elem

    def insert(self, before, name, attrs=None, data=None):
        """
        Inserts a new element as a child of this element, before the specified index or sibling.

        :param before: An :class:`XmlElement` or a numeric index to insert the new node before
        :param name: The tag name to add
        :param attrs: Attributes for the new tag
        :param data: CDATA for the new tag
        :returns: The newly-created element
        :rtype: :class:`XmlElement`
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
        Clears out all children, attributes, and data. Especially useful when using :func:`iterparse`, to release
        memory used by storing attributes, character data, and child nodes.
        """
        self.attrs = {}
        self.data = ''
        self._children = []

    def items(self):
        """
        A generator yielding ``(key, value)`` attribute pairs, sorted by key name.
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

    def _match(self, pred):
        """
        Helper function to determine if this node matches the given predicate.
        """
        if not pred:
            return True
        # Strip off the [ and ]
        pred = pred[1:-1]
        if pred.startswith('@'):
            # An attribute predicate checks the existence (and optionally value) of an attribute on this tag.
            pred = pred[1:]
            if '=' in pred:
                attr, value = pred.split('=', 1)
                if value[0] in ('"', "'"):
                    value = value[1:]
                if value[-1] in ('"', "'"):
                    value = value[:-1]
                return self.attrs.get(attr) == value
            else:
                return pred in self.attrs
        elif num_re.match(pred):
            # An index predicate checks whether we are the n-th child of our parent (0-based).
            index = int(pred)
            if index < 0:
                if self.parent:
                    # For negative indexes, count from the end of the list.
                    return self.index == (len(self.parent._children) + index)
                else:
                    # If we're the root node, the only index we could be is 0.
                    return index == 0
            else:
                return index == self.index
        else:
            if '=' in pred:
                tag, value = pred.split('=', 1)
                if value[0] in ('"', "'"):
                    value = value[1:]
                if value[-1] in ('"', "'"):
                    value = value[:-1]
                for c in self._children:
                    if c.tagname == tag and c.data == value:
                        return True
            else:
                # A plain [tag] predicate means we match if we have a child with tagname "tag".
                for c in self._children:
                    if c.tagname == pred:
                        return True
        return False

    def path(self, include_root=False):
        """
        Returns a canonical path to this element, relative to the root node.

        :param include_root: If ``True``, include the root node in the path. Defaults to ``False``.
        """
        path = '%s[%d]' % (self.tagname, self.index or 0)
        p = self.parent
        while p is not None:
            if p.parent or include_root:
                path = '%s[%d]/%s' % (p.tagname, p.index or 0, path)
            p = p.parent
        return path

    def find(self, query):
        """
        Recursively find any descendants of this node matching the given query.

        :param query: A simplified XPath query describing elements that should be returned, e.g. ``//title``,
            ``book/*``, ``*/author``, ``*/*``, etc.
        :returns: An :class:`XmlQuery` yielding matching descendants
        """
        return XmlQuery(self, query)

    def iter(self, name=None):
        """
        Recursively find any descendants of this node with the given tag name. If a tag name is omitted, this will
        yield every descendant node.

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

    def parents(self, name=None):
        """
        Yields all parents of this element, back to the root element.

        :param name: If specified, only consider elements with this tag name
        """
        p = self.parent
        while p is not None:
            if name is None or p.tagname == name:
                yield p
            p = p.parent

    def siblings(self, name=None):
        """
        Yields all siblings of this node (not including the node itself).

        :param name: If specified, only consider elements with this tag name
        """
        if self.parent and self.index:
            for c in self.parent._children:
                if c.index != self.index and (name is None or name == c.tagname):
                    yield c

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

class DrillHandler (object):

    def __init__(self, queue=None):
        self.root = None
        self.current = None
        self.queue = queue
        # Store character data in the parse handler instead of each element, to save memory.
        self.cdata = []

    def start_element(self, name, attrs):
        if self.root is None:
            self.root = XmlElement(name, attrs)
            self.current = self.root
        elif self.current is not None:
            self.current = self.current.append(name, attrs)

    def end_element(self, name):
        if self.current is not None:
            self.current.data = ''.join(self.cdata).strip()
            self.cdata = []
            if self.queue:
                self.queue.add(self.current)
            self.current = self.current.parent

    def characters(self, ch):
        if self.current is not None:
            self.cdata.append(unicode(ch))

def parse(url_or_path, encoding=None):
    """
    :param url_or_path: A file-like object, a filesystem path, a URL, or a string containing XML
    :rtype: :class:`XmlElement`
    """
    handler = DrillHandler()
    parser = expat.ParserCreate(encoding)
    parser.buffer_text = 1
    parser.StartElementHandler = handler.start_element
    parser.EndElementHandler = handler.end_element
    parser.CharacterDataHandler = handler.characters
    if isinstance(url_or_path, basestring):
        if '://' in url_or_path[:20]:
            #with contextlib.closing(url_lib.urlopen(url_or_path)) as f:
            f = contextlib.closing(url_lib.urlopen(url_or_path))
            try:    
                parser.ParseFile(f)
            except Exception, e:
                raise e
            finally:
                f.close()
        elif url_or_path[:100].strip().startswith('<'):
            if isinstance(url_or_path, unicode):
                if encoding is None:
                    encoding = 'utf-8'
                url_or_path = url_or_path.encode(encoding)
            parser.Parse(url_or_path, True)
        else:
            f = open(url_or_path, 'rb')
            try:
                parser.ParseFile(f)
            except Exception, e:
                raise e 
            finally:
                f.close()
    elif PY3 and isinstance(url_or_path, bytes):
        parser.ParseFile(bytes_io(url_or_path))
    else:
        parser.ParseFile(url_or_path)
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
            self.parser.Parse(data, not data)
            if not data:
                raise StopIteration
        return self.elements.pop(0)

    def __iter__(self):
        return self

def iterparse(filelike):
    """
    :param filelike: A file-like object with a ``read`` method
    :returns: An iterator yielding :class:`XmlElement` objects
    """
    parser = expat.ParserCreate()
    elem_iter = DrillElementIterator(filelike, parser)
    handler = DrillHandler(elem_iter)
    parser.buffer_text = 1
    parser.StartElementHandler = handler.start_element
    parser.EndElementHandler = handler.end_element
    parser.CharacterDataHandler = handler.characters
    return elem_iter