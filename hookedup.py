from collections import defaultdict

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
        self._hook = defaultdict(empty_func)
        if 'hook' in kwargs:
            self._hook.update(kwargs['hook'])

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

    def _verify_index_bounds(self, index, fxn_name='list'):
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
            return
        super().insert(index, item)
        self._hook['post-add'](item)

    def append(self, item):
        """ append item to end of list, unless pre-add function raises Abort """
        if self._hook_fxn_aborts('pre-add', item):
            return
        super().append(item)
        self._hook['post-add'](item)
        
    def pop(self, index=-1):
        """ Pop item @ index (or end of list if not supplied). If pre-remove function raises Abort,
        item will not be removed. Regardless of abort status, item will still be returned
        """
        self._verify_index_bounds(index, "pop")
        item = self[index]
        if self._hook_fxn_aborts('pre-remove', item):
            return item  # maintain expected operation in Abort, so return item w/o removing
        item = super().pop(index)
        self._hook['post-remove'](item)
        return item

    def remove(self, item):
        """ remove first instance of item from list, unless pre-remove function raises Abort """
        if item not in self:
            raise ValueError('list.remove(x): x not in list')
        if self._hook_fxn_aborts('pre-remove', item):
            return
        super().remove(item)
        self._hook['post-remove'](item)

    def __setitem__(self, index, replacement):
        """ Replace item at index in list with replacement, unless pre-replace function raises
        Abort. If setting more than one item at a time using slicing, replace items individually,
        calling pre and post-replace functions for each. After replacing items, if slicing 
        specifies more items to add, add additional items individually, calling pre and post-add 
        functions for each. If slicing specifies items to remove from list, remove items
        individually, calling pre and post-remove functions for each.
        """
        # base-case: single item replacement
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
            super().__delitem__(i)  # avoid hook call
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



class PreventOverwritingList:
    def __setattr__(self, attr_name, attr):
        if attr_name == 'children':
            if not isinstance(attr, ChildrenMonitor):
                if not isinstance(attr, list):
                    raise AttributeError('must set children to a list')
                Hook_Key = self.children._Hook_Key  # get other child's Hook Key
                attr = ChildrenMonitor(attr, Hook_Key=Hook_Key)
        super().__setattr__(attr_name, attr)



