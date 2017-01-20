# bananadbg

This is a really simple Python debugging tool. If you know how to use
Python's `>>>` prompt and a command prompt or terminal you'll learn to
use this very quickly.

```py
$ python3 bananadbg.py collections
Starting a debugging session in module 'collections' on Python 3.4.3
Type 'help' for more info.
>>> print("python commands work normally")
python commands work normally
>>> pwd
module 'collections' from '/usr/lib/python3.4/collections/__init__.py'
>>> ls
ByteString        MutableSet        __file__          _itemgetter
Callable          OrderedDict       __loader__        _proxy
ChainMap          Sequence          __name__          _recursive_repr
Container         Set               __package__       _repeat
Counter           Sized             __path__          _repr_template
Hashable          UserDict          __spec__          _starmap
ItemsView         UserList          _chain            _sys
Iterable          UserString        _class_template   abc
Iterator          ValuesView        _collections_abc  defaultdict
KeysView          _Link             _count_elements   deque
Mapping           __all__           _eq               help
MappingView       __builtins__      _field_template   namedtuple
MutableMapping    __cached__        _heapq
MutableSequence   __doc__           _iskeyword
>>> cd .abc
>>> pwd
module 'collections.abc' from '/usr/lib/python3.4/collections/abc.py'
>>> ls
ByteString       KeysView         Set              __file__
Callable         Mapping          Sized            __loader__
Container        MappingView      ValuesView       __name__
Hashable         MutableMapping   __all__          __package__
ItemsView        MutableSequence  __builtins__     __spec__
Iterable         MutableSet       __cached__       help
Iterator         Sequence         __doc__
>>> cd ..
>>> pwd
module 'collections' from '/usr/lib/python3.4/collections/__init__.py'
>>>
```
