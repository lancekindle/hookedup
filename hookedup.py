import collections

class Abort(Exception):
    """ raise this when aborting an action. Must be raised during the pre-action hook call """
    pass


class List(list):
    """ A list that can call pre- and post- hook functions for the add, remove, and replace
    operations. If the Abort exception is raised in any pre- hook call, the corresponding action
    will not take place, and will not trigger the post- hook call either.
    """

    def __init__(self, *args, **kwargs):
        """ init a list, with an optional "hook" keyword argument that supplies a dictionary
        mapping a pre-action and post-action keyword to a function
        """
        super().__init__(*args)
        empty_func = lambda: lambda *_, **__: None
        self._hook = collections.defaultdict(empty_func)
        if 'hook' in kwargs:
            self._hook.update(kwargs['hook'])

    def clear(self):
        """ remove items from list individually, starting at index 0. Call pre and post-remove
        functions for each item and do not remove item if pre-remove raises Abort.
        """
        i = 0
        while i < len(self):
            item = self[i]
            if self._hook_fxn_aborts('pre-remove', item):
                i += 1  # compensate for not removing item @ i
            else:
                super().__delitem__(i)
                self._hook['post-remove'](item)

    def extend(self, items):
        """ append items individually, calling pre and post-add functions. If pre-add function
        raises Abort, will not add that item.
        """
        if not isinstance(items, collections.Iterable):
            obj_type = str(type(items)).replace('>', '').replace('<class ', '')
            raise TypeError(obj_type + ' object is not iterable')
        for item in items:
            self.append(item)  # recursive. Will trigger pre and post hooks in append fxn

    def _hook_fxn_aborts(self, hook_name, *args):
        """ run the named hook with supplied arguments, and return whether function raised Abort 
        Error or not.
        Returns: True or False
        """
        try:
            self._hook[hook_name](*args)
        except Abort:
            return True
        return False

    def _verify_index_bounds(self, index, fxn_name='list assignment'):
        """ determine from provided index if operation would trigger index error. If it does, raise
        IndexError. If calling from a pop function, set optional fxn_name to "pop"
        params:
        index: integer index at which to access an element inside list
        fxn_name: optional name to use instead of "list" when raising error

        Returns: None. May raise IndexError instead
        """
        length = len(self)
        if length == 0 or index >= length or index < -length:
            raise IndexError(fxn_name + ' index out of range')

    def insert(self, index, item):
        """ insert item into list at given index, unless pre-add function raises Abort. """
        if self._hook_fxn_aborts('pre-add', item):
            super().insert(index, item)
            self._hook['post-add'](item)

    def append(self, item):
        """ append item to end of list, unless pre-add function raises Abort """
        if not self._hook_fxn_aborts('pre-add', item):
            super().append(item)
            self._hook['post-add'](item)
        
    def pop(self, index=-1):
        """ Pop item @ index (or end of list if not supplied). If pre-remove function raises Abort,
        item will not be removed. Regardless of abort status, item will still be returned
        """
        self._verify_index_bounds(index, "pop")
        item = self[index]
        if self._hook_fxn_aborts('pre-remove', item):
            return item  # return expected value even in Abort: return item w/o removing from list
        item = super().pop(index)
        self._hook['post-remove'](item)
        return item

    def remove(self, item):
        """ remove first instance of item from list, unless pre-remove function raises Abort """
        if item not in self:
            raise ValueError('list.remove(x): x not in list')
        if not self._hook_fxn_aborts('pre-remove', item):
            super().remove(item)
            self._hook['post-remove'](item)

    def __iadd__(self, items):
        """ in-place add items. It is the same as extend(), but we must implement both here so that
        pre and post hooks are called properly
        """
        self.extend(items)

    def __delitem__(self, index):
        self._verify_index_bounds(index)
        item = self[index]
        if not self._hook_fxn_aborts('pre-remove', item):
            super().__delitem__(index)
            self._hook['post-remove'](item)


    def __setitem__(self, index, replacement):
        """ Replace item at index in list with replacement, unless pre-replace function raises
        Abort. If setting more than one item at a time using slicing, replace items individually,
        calling pre and post-replace functions for each. After replacing items, if slicing 
        specifies more items to add, add additional items individually, calling pre and post-add 
        functions for each. If slicing specifies items to remove from list, remove items
        individually, calling pre and post-remove functions for each.
        """
        if type(index) == int:
            self._verify_index_bounds(index)
            item = self[index]
            if self._hook_fxn_aborts('pre-replace', item, replacement):
                return
            super().__setitem__(index, replacement)
            self._hook['post-replace'](item, replacement)
            return
        list_slice = self[index]  # trigger standard error if index is not slice
        self._verify_slices_are_valid(index, list_slice, replacement)
        last_index = self._replace_corresponding_items_in_both_slices(index, list_slice, 
                                                                      replacement)
        overflow = len(list_slice) - len(replacement)
        if overflow > 0:
            self._remove_remaining_items_in_list_slice(last_index, overflow)
        if overflow < 0:
            self._add_remaining_items_in_replacement_slice(last_index, overflow, replacement)

    def _verify_slices_are_valid(self, index, list_slice, replacement_slice):
        """ verify that given slice (index) defines a valid slice given replacement_slice. In
        general, if slice is standard (step-size of 1), slice will be valid. If step size is not
        standard, list_slice and replacement_slice must be equal in length. If slice is invalid,
        raise ValueError
        """
        if not type(index) == slice:
            raise TypeError('list indices must be integer or slice, not ' + str(type(index)))
        if index.step is not None and index.step != 1:
            if len(list_slice) != len(replacement_slice):
                raise ValueError('attempt to assign sequence of size ' + str(len(replacement_slice))
                                 + ' to extended slice of size ' + str(len(list_slice)))

    def _replace_corresponding_items_in_both_slices(self, index, list_slice, replacement):
        """ for as long as both slices have an item at a given index, replace list_slice's 
        respective item in the list with replacement's item. Operation will end after either slice
        has been fully iterated over.
        Returns: index just after replacement operation ends. Can begin insert or remove from there
        """
        i = index.start
        slice_range = index.indices(len(self))
        for i, _, replacingItem in zip(range(*slice_range), list_slice, replacement):
            self[i] = replacingItem  # recursive __setitem__ call will trigger pre, post hooks
            i += 1  # compensate for adding/removing additional items after for-loop
        return i

    def _remove_remaining_items_in_list_slice(self, i, overflow):
        """ remove overflow # of items from list, starting at index i, and call pre-remove and
        post-remove functions. Will not remove item if pre-remove raises Abort
        """
        while overflow > 0:
            item = self[i]
            if self._hook_fxn_aborts('pre-remove', item):
                i += 1  # avoid visiting same item
                continue
            super().__delitem__(i)
            self._hook['post-remove'](item)
            overflow -= 1

    def _add_remaining_items_in_replacement_slice(self, i, overflow, replacement):
        """ insert remaining items in replacement slice to self list, unless pre-add aborts """
        for repl_index in range(overflow, 0, 1):
            item = replacement[repl_index]
            if not self._hook_fxn_aborts('pre-add', item):
                super().insert(i, item)
                i += 1
                self._hook['post-add'](item)



class PreventHookedupOverwriteReset:
    """ inherit from this to prevent a hookedup List from being overwritten and/or reset. When user
    attempts to set attribute of inheriting class, if attribute already on class is a hookedup
    List, this raises AttributeError. User instead should use.clear() to attempt to clear attribute
    and then update it accordingly.
    for example:
    Class Example(PreventHookedupOverwriteReset):
        pass
    a = A()
    a.list = hookedup.List()  # a.list cannot be reset or set to anything else once it has been set
                              # to hookedup.List
    a.list = []  # raises AttributeError
    a.list = hookedup.List()  # also raises AttributeError
    """

    def __setattr__(self, attr_name, attr):
        try:
            original = getattr(self, attr_name)
        except AttributeError:
            super().__setattr__(self, attr_name, attr)
            return
        for hookedType in (List,):
            if isinstance(original, hookedType):
                raise AttributeError('Overwriting attribute "' + attr_name + '" of type ' +
                                     str(hookedType) + 'prohibited')
        super().__setattr__(attr_name, attr)



