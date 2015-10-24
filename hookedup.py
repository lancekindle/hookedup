from collections import defaultdict

class Abort(Exception):
    pass  # raise this when 


class List(list):
    """ mimicks a list, but listens to any calls that might change the list. If any part is
    changed in any way, it calls the appropriate hook.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        empty_func = lambda: lambda *_, **__: None
        self._hook = defaultdict(empty_func)
        if 'hook' in kwargs:
            self._hook.update(kwargs['hook'])

    def _hook_fxn_aborts(self, hook_name, *args):
        """ run the hook with supplied arguments, and return whether function raised Abort Error or
        not
        Returns: True or False
        """
        try:
            self._hook[hook_name](*args)
        except Abort:
            return True
        return False

    def _trigger_index_error_if_applicable(self, index, fxn, *args):
        """ determine from provided index if operation would trigger index error. If it would, call
        provided function with supplied arguments to trigger native exception.
        params:
        index: integer index at which to access an element inside list
        fxn: typically a super().fxn to call if IndexError were to trigger
        args: any arguments to pass to fxn

        Returns: None. May raise and IndexError instead
        """
        length = len(self)
        if length == 0 or index >= length or index < -length:
            #raise IndexError('list index out of range')
            fxn(*args)  # trigger exception

    def insert(self, index, item):
        if self._hook_fxn_aborts('pre-add', item):
            return
        super().insert(index, item)
        self._hook['post-add'](item)

    def append(self, item):
        if self._hook_fxn_aborts('pre-add', item):
            return
        super().append(item)
        self._hook['post-add'](item)
        
    def pop(self, index=-1):
        """ Pop item @ index (or end of list if not supplied). Regardless of Abort status, return
        item. (but Abort will prevent item removal)
        """
        self._trigger_index_error_if_applicable(index, super().pop, index)
        item = self[index]
        if self._hook_fxn_aborts('pre-remove', item):
            return item  # maintain expected operation in Abort, so return item w/o removing
        item = super().pop(index)
        self._hook['post-remove'](item)
        return item

    def remove(self, item):
        if item not in self:
            super().remove(item)  # trigger standard ValueError 
        if self._hook_fxn_aborts('pre-remove', item):
            return
        super().remove(item)
        self._hook['post-remove'](item)

    def __setitem__(self, index, replacement):
        # base-case: single item replacement
        if type(index) == int:
            self._trigger_index_error_if_applicable(index, super().__setitem__, index, replacement)
            item = self[index]
            if self._hook_fxn_aborts('pre-replace', item, replacement):
                return
            super().__setitem__(index, replacement)
            self._hook['post-replace'](item, replacement)
            return
# index is a slice. First we check that we do not generate a ValueError on Extended Slice
        if not type(index) == slice:
            raise TypeError('list indices must be integers, not ' + str(type(index)))
        extended_slice = self[index]
        if index.step is not None and index.step != 1:
            if len(extended_slice) != len(replacement):
                super().__setitem__(index, replacement)  # trigger ValueError for extended slice
        # if we make it here, then slice is valid, extended_slice is valid. Now we determine how
        # many elements are being replaced vs. how many are being inserted/removed.
        replaceCount = 0
        for i, _, replacingItem in zip(range(*index.indices(len(self))), extended_slice,
                                     replacement):
            self[i] = replacingItem
            replaceCount += 1
            i += 1  # compensatation if adding/removing additional items after for-loop
        # just finished replacing items. Now we either add or remove items
# remove additional items
        overflow = len(extended_slice) - len(replacement)
# if overflow < 0 we have items to add. If overflow > 0 we have items to remove
        while overflow > 0:
            item = self[i]
            if self._hook_fxn_aborts('pre-remove', item):
                i += 1  # avoid getting same item
                continue
            super.().__delitem__(i)  # avoid hook call
            self._hook['post-remove'](item)
            overflow -= 1
        # overflow < 0 equals items we must add to list using insert @ i
        while overflow < 0:
            replacingItem = re
            
            


class PreventOverwritingList:
    def __setattr__(self, attr_name, attr):
        if attr_name == 'children':
            if not isinstance(attr, ChildrenMonitor):
                if not isinstance(attr, list):
                    raise AttributeError('must set children to a list')
                Hook_Key = self.children._Hook_Key  # get other child's Hook Key
                attr = ChildrenMonitor(attr, Hook_Key=Hook_Key)
        super().__setattr__(attr_name, attr)



