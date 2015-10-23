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
        item
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
        if not type(index) == slice:
            self._trigger_index_error_if_applicable(index, super().__setitem__, index, replacement)
            item = self[index]
            if self._hook_fxn_aborts('pre-replace', item, replacement):
                return
            super().__setitem__(index, replacement)
            self._hook['post-replace'](item, replacement)
            return
# index is a slice. First we check that we do not generate a ValueError on Extended Slice
        extended_slice = self[index]
        if index.step is not None and index.step != 1:
            if len(extended_slice) != len(replacement):
                super().__setitem__(index, replacement)  # trigger ValueError for extended slice
        # if we make it here, then slice is valid, extended_slice is valid. Now we determine how
        # many elements are being replaced vs. how many are being inserted/removed.
# 2nd case: multi-item replacement (which may include greater or fewer elements than selection)
        children = self[index]
        replacements = element
        i = index.start
        for i, _, element in zip(range(index.start, index.stop, index.step), children, 
                                     replacements):  # stop when children/replacements depleted
            self[i] = element
            i += 1  # compensate for ending index to begin inserting additional elements
# determine if we have remaining items to insert / remove
        #if len(children) > len(replacements):
# the remaining children must be removed from list. Remove via index instead of .remove to maintain
# desired operation, since using .remove will remove first instance. Whereas this use case clearly
# indicated a slice of elements to remove
            

        #if len(replacements) > len(children):
        

class PreventOverwritingList:
    def __setattr__(self, attr_name, attr):
        if attr_name == 'children':
            if not isinstance(attr, ChildrenMonitor):
                if not isinstance(attr, list):
                    raise AttributeError('must set children to a list')
                Hook_Key = self.children._Hook_Key  # get other child's Hook Key
                attr = ChildrenMonitor(attr, Hook_Key=Hook_Key)
        super().__setattr__(attr_name, attr)



