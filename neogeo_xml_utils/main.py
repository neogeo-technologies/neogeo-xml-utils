import re
from collections import OrderedDict
from sys import version_info
from xml.etree.ElementTree import tostring as et_tostring
from xml.etree.ElementTree import Element, SubElement, XMLParser
from xml.etree.ElementTree import register_namespace


__all__ = ['XMLToObj', 'ObjToXML']


class XMLToObj:

    def __init__(self, text, attrib_tag='@', text_tag='$', with_ns=True):

        self.text = text
        self.attrib_tag = attrib_tag
        self.text_tag = text_tag
        self.with_ns = with_ns

    def _proceed(self):

        class Parser:

            def __init__(self, attrib_tag='@', text_tag='$', with_ns=True):
                self.attrib_tag = attrib_tag
                self.text_tag = text_tag
                self.with_ns = with_ns

                self.__obj = OrderedDict()
                self.__cur = None
                self.__attr = None
                self.__pos = 0
                self.__path = OrderedDict()
                self.__data = []
                self.__namespaces = {}
                self.__count_ns = 0

            def start(self, tag, attrib):

                def parse_tag(val):
                    uri = None
                    m = re.match('^{(.+)}(\w+)$', val)
                    if m and len(m.groups()) == 2:
                        uri, val = m.groups()
                    return uri, val

                def parse_attribute(d, prefix='@'):
                    r = OrderedDict()
                    for k, v in d.items():
                        if not self.with_ns:
                            _, k = parse_tag(k)
                        r['{0}{1}'.format(prefix, k)] = v
                    return r

                def recur_n_insert(tree, depth):
                    path = self.__path
                    pos = self.__pos
                    cur = self.__cur
                    attr = self.__attr

                    keys = list(tree.keys())  # This requires OrderedDict!

                    if depth < pos:
                        last = keys[-1]
                        val = tree[last]
                        if last == path[depth]:
                            if isinstance(val, list):
                                val = val[-1]
                            depth += 1
                            recur_n_insert(val, depth)

                    elif depth == pos:
                        if cur in iter(keys):
                            if not isinstance(tree[cur], list):
                                tree[cur] = [tree[cur]]
                            tree[cur].append(attr)
                        else:
                            tree[cur] = attr

                if not self.with_ns:
                    _, self.__cur = parse_tag(tag)
                else:
                    self.__cur = tag

                self.__attr = OrderedDict()
                if attrib:
                    self.__attr = parse_attribute(
                                            attrib, prefix=self.attrib_tag)

                recur_n_insert(self.__obj, 0)
                self.__path.update({self.__pos: self.__cur})
                self.__pos += 1

            def data(self, data):

                if data.strip():
                    self.__data.append(data)

            def end(self, _):

                def browse_n_update(tree, cur, txt):

                    for key, subtree in tree.items():
                        if key == cur:
                            if not subtree:
                                tree[key] = txt
                                break

                            if isinstance(subtree, dict):
                                subtree[self.text_tag] = txt

                            if isinstance(subtree, list):
                                if isinstance(subtree[-1], dict):
                                    if not subtree[-1]:
                                        subtree[-1] = txt
                                    else:
                                        subtree[-1][self.text_tag] = txt

                        if isinstance(subtree, list):
                            subtree = subtree[-1]

                        if isinstance(subtree, dict):
                            browse_n_update(subtree, cur, txt)

                if len(self.__data) > 0:
                    browse_n_update(
                            self.__obj, self.__cur, ''.join(self.__data))

                self.__data = []
                self.__pos -= 1
                del self.__path[self.__pos]

            def close(self):

                def clean(obj):
                    if isinstance(obj, OrderedDict):
                        obj = dict(obj) or None
                    if isinstance(obj, (list, tuple, set)):
                        return type(obj)(clean(x) for x in obj if x is not None)
                    elif isinstance(obj, dict):
                        return type(obj)(
                            (clean(k), clean(v)) for k, v in obj.items())
                    else:
                        return obj

                copy = self.__obj.copy()
                self.__init__(
                        attrib_tag=self.attrib_tag, text_tag=self.text_tag)

                return clean(copy)

        target = Parser(attrib_tag=self.attrib_tag,
                        text_tag=self.text_tag,
                        with_ns=self.with_ns)

        parser = XMLParser(target=target)
        parser.feed(self.text)

        return parser.close()

    def retrieve_namespaces(self):

        if version_info < (3, 4):
            raise NotImplementedError('Python 3.4 or higher is required.')

        from xml.etree.ElementTree import XMLPullParser

        ns = {}
        parser = XMLPullParser(['start-ns'])
        parser.feed(self.text)
        for e in parser._events_queue:
            if e[0] != 'start-ns':
                continue
            prefix, uri = e[1]
            if uri not in ns.keys():
                ns[uri] = prefix

        return dict((v, k) for k, v in ns.items())

    @property
    def data(self):
        return self._proceed()


class ObjToXML:

    def __init__(self, obj, attrib_tag='@', text_tag='$', ns=None):
        self.obj = obj
        self.attrib_tag = attrib_tag
        self.text_tag = text_tag
        self.ns = ns or {}

    def _proceed(self):

        def build(elt, tag):
            return SubElement(elt, tag)

        def browse(tree, parent, cb):
            if isinstance(tree, str):
                parent.text = tree

            if isinstance(tree, dict):
                for key, val in tree.items():

                    m = re.match('^{(.+)}(\w+)$', key)
                    if m and len(m.groups()) == 2:
                        ns = m.groups()[0]
                        tag = m.groups()[1]
                        if ns in self.ns.keys():
                            key = '{{{0}}}{1}'.format(self.ns[ns], tag)

                    if key.startswith(self.attrib_tag):
                        k = re.sub('({0})(.+)'.format(
                                                self.attrib_tag), '\g<2>', key)
                        parent.set(k, val)
                        continue

                    if key == self.text_tag:
                        parent.text = val
                        continue

                    if isinstance(val, list):
                        for elt in val:
                            browse(elt, cb(parent, key), cb)
                        continue

                    browse(val, cb(parent, key), cb)

        for prefix, uri in self.ns.items():
            register_namespace(prefix, uri)

        base = None
        if len(self.obj.keys()) < 1:
            pass
        elif len(self.obj.keys()) > 1:
            base = Element('root')
        else:
            for root, sub in self.obj.items():
                base = Element(root)
                browse(sub, base, build)

        return base

    def tostring(self, *args, **kwargs):
        return et_tostring(self.tree, *args, **kwargs)

    @property
    def tree(self):
        return self._proceed()
