# neogeo-xml-utils

# Installation

    >>> pip install git+https://github.com/neogeo-technologies/neogeo-xml-utils.git

## Usages

### XMLToObj(text, **opts)

Convert an XML string to an object.

Options:

*   `attrib_tag`: (default=`'@'`)
*   `text_tag`: (default=`'$'`)
*   `with_ns`: (boolean, default=`True`)

#### properties

*   __data__

#### methods

*   __retrieve_ns()__ (Python 3.4+ only) Returns a dictionary with prefixes and URI.

#### Example

```
>>> from neogeo_xml_utils import XMLToObj
>>> text = '''<a><b>0</b><b>1</b><b>2</b><b><c foo="bar">3</c></b><b><c foo="bar">4</c></b><b><c foo="bar">5</c></b></a>'''
>>> xo = XMLToObj(text)
>>> xo.data
{'a': {'b': ['0', '1', '2', {'c': {'$': '3', '@foo': 'bar'}}, {'c': {'$': '4', '@foo': 'bar'}}, {'c': {'$': '5', '@foo': 'bar'}}]}}

```

### ObjToXML(obj, **opts)

Convert an object to an XML string.

Options:

*   `attrib_tag`: (default=`'@'`)
*   `text_tag`: (default=`'$'`)
*   `ns`: A dictionary with prefixes and URI.

#### properties

*   __tree__: the XML element tree.

#### methods

*   __tostring()__ -> __xml.etree.ElementTree.tostring__

#### Example

```
>>> from neogeo_xml_utils import ObjToXML
>>> obj = {'a': {'b': ['0', '1', '2', {'c': {'$': '3', '@foo': 'bar'}}, {'c': {'$': '4', '@foo': 'bar'}}, {'c': {'$': '5', '@foo': 'bar'}}]}}
>>> ox = ObjToXML(obj)
>>> ox.tostring()
<a><b>0</b><b>1</b><b>2</b><b><c foo="bar">3</c></b><b><c foo="bar">4</c></b><b><c foo="bar">5</c></b></a>
```
