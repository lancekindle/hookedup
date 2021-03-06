import collections
import warnings

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
        keywords = set(['pre_add', 'pre_remove', 'pre_replace', 
                        'post_add', 'post_remove', 'post_replace'])
        super().__init__(*args)
        empty_func = lambda: lambda *_, **__: None
        self._hook = collections.defaultdict(empty_func)
        self._abort_stats = collections.defaultdict(int)
        self._hook.update(kwargs)
        unrecognized = set(kwargs.keys()) - keywords
        if unrecognized:
            warnings.warn('unrecognized keywords passed to hookedup.List: ' + str(unrecognized))

    def clear(self):
        """ remove items from list individually, starting at index 0. Call pre and post_remove
        functions for each item and do not remove item if pre_remove raises Abort.
        """
        i = 0
        while i < len(self):
            item = self[i]
            if self._hook_fxn_aborts('pre_remove', item):
                i += 1  # compensate for not removing item @ i
            else:
                super().__delitem__(i)
                self._call_post_hook_fxn('post_remove', item)

    def extend(self, items):
        """ append items individually, calling pre and post_add functions. If pre_add function
        raises Abort, will not add that item.
        """
        if not isinstance(items, collections.Iterable):
            obj_type = str(type(items)).replace('>', '').replace('<class ', '')
            raise TypeError(obj_type + ' object is not iterable')
        for item in items:
            self.append(item)  # recursive. Will trigger pre and post hooks in append fxn

    def _call_post_hook_fxn(self, hook_name, *args):
        """ run the named hook with supplied arguments """
        self._hook[hook_name](self, *args)

    def _hook_fxn_aborts(self, hook_name, *args):
        """ run the named hook with supplied arguments, and return whether function raised Abort 
        Error or not.
        Returns: True or False
        """
        try:
            self._hook[hook_name](self, *args)
        except Abort:
            self._abort_stats[hook_name] += 1
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
        """ insert item into list at given index, unless pre_add function raises Abort. """
        if self._hook_fxn_aborts('pre_add', item):
            super().insert(index, item)
            self._call_post_hook_fxn('post_add', item)

    def append(self, item):
        """ append item to end of list, unless pre_add function raises Abort """
        if not self._hook_fxn_aborts('pre_add', item):
            super().append(item)
            self._call_post_hook_fxn('post_add', item)
        
    def pop(self, index=-1):
        """ Pop item @ index (or end of list if not supplied). If pre_remove function raises Abort,
        item will not be removed. Regardless of abort status, item will still be returned
        """
        self._verify_index_bounds(index, "pop")
        item = self[index]
        if self._hook_fxn_aborts('pre_remove', item):
            return item  # return expected value even in Abort: return item w/o removing from list
        item = super().pop(index)
        self._call_post_hook_fxn('post_remove', item)
        return item

    def remove(self, item):
        """ remove first instance of item from list, unless pre_remove function raises Abort """
        if item not in self:
            raise ValueError('list.remove(x): x not in list')
        if not self._hook_fxn_aborts('pre_remove', item):
            super().remove(item)
            self._call_post_hook_fxn('post_remove', item)

    def __iadd__(self, items):
        """ in-place add items. It is the same as extend(), but we must implement both here so that
        pre and post hooks are called properly
        """
        self.extend(items)
        return self

    def __imul__(self, multiplier):
        if not isinstance(multiplier, int):
            obj_type = str(type(multiplier)).replace('>', '').replace('<class ', '')
            raise TypeError(obj_type + 'object cannot be interpreted as an integer')
        if multiplier <= 0:
            return self.clear()
        original = list(self)
        for i in range(1, multiplier):
            self.extend(original)
        return self

    def __delitem__(self, index):
        """ If index is an integer, delete item @ given index, calling pre and post remove hooks
        appropriately. If index is a slice, remove specified index range, calling pre and post
        hooks for each item as it removes them. Due to the delitem's similarity to setitem, I have
        borrowed several functions used in setitem to only delete the range specified by slice
        """
        if type(index) == int:
            self._verify_index_bounds(index)
            item = self[index]
            if not self._hook_fxn_aborts('pre_remove', item):
                super().__delitem__(index)
                self._call_post_hook_fxn('post_remove', item)
            return
        list_slice = self[index]  # trigger standard error if index is not slice
        last_index = self._replace_corresponding_items_in_both_slices(index, list_slice, [])
        overflow = len(list_slice)
        self._remove_remaining_items_in_list_slice(index, last_index, overflow)

    def __setitem__(self, index, replacement):
        """ Replace item at index in list with replacement, unless pre_replace function raises
        Abort. If setting more than one item at a time using slicing, replace items individually,
        calling pre and post_replace functions for each. After replacing items, if slicing 
        specifies more items to add, add additional items individually, calling pre and post_add 
        functions for each. If slicing specifies items to remove from list, remove items
        individually, calling pre and post_remove functions for each.
        self[0:3] = [0,1]  # replace two items on list (index 0 & 1) with two items
        self[0:3] = [0]  # replace one item on list (index 0), and remove other item (index 1) from list
        self[0:3] = [0,1,2]  # replace two items on list (index 0 & 1) with first two items on
                    list, then insert last item (2) into list @ end of replacement index (index 2)
        """
        if type(index) == int:
            self._verify_index_bounds(index)
            item = self[index]
            if not self._hook_fxn_aborts('pre_replace', item, replacement):
                super().__setitem__(index, replacement)
                self._call_post_hook_fxn('post_replace', item, replacement)
            return
        list_slice = self[index]  # trigger standard error if index is not slice
        replacement = list(replacement)  # all fxns below expect a list-like object.
        self._verify_slices_are_valid(index, list_slice, replacement)
        last_index = self._replace_corresponding_items_in_both_slices(index, list_slice, 
                                                                      replacement)
        overflow = len(list_slice) - len(replacement)
        if overflow > 0:
            self._remove_remaining_items_in_list_slice(index, last_index, overflow)
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
            if index.step == 0:
                raise ValueError('slice step cannot be zero')
            if len(list_slice) != len(replacement_slice):
                raise ValueError('attempt to assign sequence of size ' + str(len(replacement_slice))
                                 + ' to extended slice of size ' + str(len(list_slice)))

    def _replace_corresponding_items_in_both_slices(self, index, list_slice, replacement):
        """ for as long as both slices have an item at a given index, replace list_slice's 
        respective item in the list with replacement's item. Operation will end after either slice
        has been fully iterated over.
        Returns: index just after replacement operation ends. Can begin insert or remove from there
        """
        slice_range = index.indices(len(self))
        i = slice_range[0]  # normally index.start, but adjusted to list size
        for i, _, replacingItem in zip(range(*slice_range), list_slice, replacement):
            self[i] = replacingItem  # recursive __setitem__ call will trigger pre, post hooks
            i += 1  # compensate for adding/removing additional items after for-loop
        return i

    def _remove_remaining_items_in_list_slice(self, islice, i, overflow):
        """ attempt to remove overflow # of items from list, starting at index i, and call
        pre_remove and post_remove functions. Will not remove item if pre_remove raises Abort
        """
        step = islice.step or 1
        for _ in range(overflow):
            item = self[i]
            if self._hook_fxn_aborts('pre_remove', item):
                i += step  # avoid removal attempt of same item
                continue
            super().__delitem__(i)
            self._call_post_hook_fxn('post_remove', item)
            if step > 0:
                i += step - 1  # normally 0, but compensdated for larger step-sizes
            else:
                i += step  # negative steps do not need compensation for removing at an index

    def _add_remaining_items_in_replacement_slice(self, i, overflow, replacement):
        """ insert remaining items in replacement slice to self list, unless pre_add aborts.
        overflow: a negative number whose absolute value indicate the number of items to insert
        """
        for repl_index in range(overflow, 0, 1):
            item = replacement[repl_index]
            if not self._hook_fxn_aborts('pre_add', item):
                super().insert(i, item)
                i += 1
                self._call_post_hook_fxn('post_add', item)


class PreventOverwriteProperty:
    
    @classmethod
    def setup(cls, *args, **kwargs):
        """setup for property(). Inside a separate class, call
        property(PreventOverwriteProperty(L, **hooks)) where 
        L is a premade list you want each time, and **hooks is a dictionary of
        the hooks you want installed in the list. Each time an owner accesses
        it's list, it will get the same list (created the first time it's
        accessed, and found in a dictionary each time after that)
        """
        self = cls()
        self._owners = {}
        construct_list = lambda: List(*args, **kwargs)

        def getter(owner):
            if owner in self._owners:
                return self._owners[owner]
            L = construct_list()
            self._owners[owner] = L
            return L

        return getter


class PreventHookedupOverwriteReset:
    """ inherit from this to prevent a hookedup List from being overwritten and/or reset. When user
    attempts to set attribute of inheriting class, if attribute already on class is a hookedup
    List, this raises AttributeError (unless it is the same object, as a case would be when using
    *= or +=). User instead should use.clear() to attempt to clear attribute and then update it 
    accordingly.
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
            super().__setattr__(attr_name, attr)  # allow setting attribute first time
            return
        if original is attr:
            super().__setattr__(attr_name, attr)  # allows __iadd__ (+=) and __imul__ (*=) to work
            return
        for hookedType in (List,):
            if isinstance(original, hookedType):
                raise AttributeError('Overwriting attribute "' + attr_name + '" of type ' +
                                     str(hookedType) + 'prohibited')
        super().__setattr__(attr_name, attr)



