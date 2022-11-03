import collections


class SkipFilter(object):

    def __init__(self, types=None, keys=None, allow_empty=False):
        self.types = tuple(types or [])
        self.keys = set(keys or [])
        self.allow_empty = allow_empty  # if True include empty filtered structures

    def filter(self, data):
        if isinstance(data, collections.Mapping):
            result = {}  # dict-like, use dict as a base
            for k, v in data.items():
                if k in self.keys or isinstance(v, self.types):  # skip key/type
                    continue
                try:
                    result[k] = self.filter(v)
                except ValueError:
                    pass
            if result or self.allow_empty:
                return result
        elif isinstance(data, collections.Sequence):
            result = []  # a sequence, use list as a base
            for v in data:
                if isinstance(v, self.types):  # skip type
                    continue
                try:
                    result.append(self.filter(v))
                except ValueError:
                    pass
            if result or self.allow_empty:
                return result
        else:  # we don't know how to traverse this structure...
            return data  # return it as-is, hope for the best...
        raise ValueError