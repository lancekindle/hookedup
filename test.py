import unittest
import hookedup
import random

class TestListUnimplementedParts(unittest.TestCase):
    """ verify that these unimplemented methods do not return a hookedup.List instance; only a list
    """

    def setUp(self):
        self.original = list(range(4))
        self.L = hookedup.List(self.original)
        self.list = list(self.original)

    def test_L_is_hookedup_instance(self):
        self.assertTrue(isinstance(self.L, hookedup.List))

    def test_list_add_returns_normal_list(self):
        """ verify that addition in both arrangements produces a normal list """
        L = self.L + self.original
        L2 = self.original + self.L
        self.assertFalse(isinstance(L, hookedup.List))
        self.assertFalse(isinstance(L2, hookedup.List))
        self.assertTrue(isinstance(L, list))
        self.assertTrue(isinstance(L2, list))

    def test_list_multiply_returns_normal_list(self):
        """ verify that multiplication in multiple arrangments always produces a normal list """
        L = self.L * 2
        L2 = 2 * self.L
        self.assertFalse(isinstance(L, hookedup.List))
        self.assertFalse(isinstance(L2, hookedup.List))
        self.assertTrue(isinstance(L, list))
        self.assertTrue(isinstance(L2, list))

    def test_copy_returns_normal_list(self):
        L = self.L.copy()
        self.assertTrue(isinstance(L, list))
        self.assertFalse(isinstance(L, hookedup.List))



class TestAllListOperations(unittest.TestCase):
    """ verify that normal operation and exceptions are the same between hookedup.List and list """
    
    def setUp(self):
        self.original = list(range(4))
        self.L = hookedup.List(self.original)
        self.list = list(self.original)

    def test_lists_are_equal(self):
        self.assertTrue(self.L == self.original == self.list)


class TestHookedupList(unittest.TestCase):
    """ test implemented methods of hookedup.List. Including that pre- and post- hooks are called
    for each hooked operation. Also verify that aborting operation works as expected
    """

    def setUp(self):
        self.count = 0
        self.original = list(range(4))
        self.list = list(self.original)
        self.L = hookedup.List(self.original)
        self.post_hooks = ['post_add', 'post_replace', 'post_remove']
        self.pre_hooks = ['pre_add', 'pre_replace', 'pre_remove']

    def test_lists_are_equal_and_correct_instance(self):
        self.assertTrue(self.L == self.original == self.list)
        self.assertTrue(len(self.original) == 4)
        self.assertTrue(isinstance(self.L, hookedup.List))
        self.assertFalse(isinstance(self.list, hookedup.List))
        
    def increment_count(self, *_):
        self.count += 1

    def raise_abort(self, *_):
        raise hookedup.Abort()

    def increment_and_abort(self, *_):
        self.increment_count()
        self.raise_abort()

    def test_iadd(self):
        L = hookedup.List()
        L += self.list
        self.assertTrue(L == self.list)
        self.assertTrue(isinstance(L, hookedup.List))
        hold_only_4_items = lambda *_: (len(self.L2) >= 4 and self.increment_and_abort())
        self.L2 = hookedup.List(pre_add=hold_only_4_items)
        self.L2 += self.list
        self.assertTrue(self.L2 == L)
        self.L2 += self.list
        self.assertTrue(self.L2 == L == self.original)
        self.assertTrue(len(self.L2) == len(self.original) == self.count)
        self.assertTrue(isinstance(self.L2, hookedup.List))
        self.assertTrue(isinstance(L, hookedup.List))

    def test_imul(self):
        hold_only_4_items = lambda *_: (len(self.L2) >= 4 and self.increment_and_abort())
        self.L2 = hookedup.List(self.original, pre_add=hold_only_4_items)
        self.list *= 3
        self.L *= 3
        self.L2 *= 3
        self.assertTrue(self.L == self.list)
        self.assertTrue(len(self.original) * 2 == self.count)
        self.assertTrue(self.original == self.L2)
        self.assertTrue(isinstance(self.L, hookedup.List))
        self.assertTrue(isinstance(self.L2, hookedup.List))

    def test_delitem_int_index(self):
        L2 = hookedup.List(self.list, pre_remove=self.increment_and_abort)
        self.assertTrue(self.list == self.L == L2)
        for _ in self.original:
            del self.list[0]
            del self.L[0]
            del L2[0]
        self.assertTrue([] == self.list == self.L)
        self.assertTrue(L2 == self.original)
        self.assertTrue(self.count == len(self.original))
        self.assertTrue(isinstance(self.L, hookedup.List))
        self.assertTrue(isinstance(L2, hookedup.List))

    def test_delitem_slice(self):
        """ verify that deleting slices in hooked.List matches list behavior. Also verify that
        aborted slice deletion does not delete the abort-deleted item
        """
        slices = [slice(1,2), slice(1,3), slice(1,4,2), slice(0,5,2), slice(4, 0, -1), 
                  slice(3, None, -1), slice(3, None, -2)]
        for s in slices:
            self.setUp()  # reset lists and count
            L2 = hookedup.List(self.original, pre_remove=self.increment_and_abort)
            self.list.__delitem__(s)
            self.L.__delitem__(s)
            L2.__delitem__(s)
            difference = len(self.original) - len(self.list)
            self.assertTrue(self.list == self.L)
            self.assertTrue(L2 == self.original)
            self.assertTrue(difference == self.count)

    def test_clear(self):
        L2 = hookedup.List(self.list, pre_remove=self.increment_and_abort)
        self.assertTrue(self.L == self.list == L2)
        self.L.clear()
        self.assertTrue(len(self.L) == self.count == 0)
        self.assertTrue(len(self.list) == len(L2) == 4)
        L2.clear()
        self.assertTrue(L2 == self.list)
        self.assertTrue(len(L2) == self.count == 4)

    def test_extend(self):
        L = hookedup.List()
        L.extend(self.list)
        self.assertRaises(TypeError, L.extend, 4)
        self.assertTrue(self.list == L)
        L.extend([])
        self.assertTrue(self.list == L)
        L = hookedup.List(pre_add=self.increment_and_abort)
        L.extend(self.list)
        self.assertTrue(self.count == len(self.list))
        self.assertTrue(len(L) == 0)

    def test_list_inits_with_empty_hook_or_no_hook(self):
        L = hookedup.List(**{})
        L = hookedup.List()

    def test_random_valid_hooks(self):
        valid_hooks = self.post_hooks + self.pre_hooks
        count = 1
        while valid_hooks:
            hooks = {}
            hook_event = random.choice(valid_hooks)
            valid_hooks.remove(hook_event)
            hooks[hook_event] = self.increment_count
            L = hookedup.List(**hooks)
            self.trigger_all_hooks(L)
            self.assertTrue(count == self.count)
            count += 1

    def test_list_inits_with_various_iterables(self):
        iterables = [(0,1,2), range(3), [0,1,2], {x: None for x in range(3)}]
        for iterable in iterables:
            ll = hookedup.List(iterable)
            self.assertTrue(len(ll) == 3)
            self.assertTrue(ll == [0,1,2])

    def trigger_all_hooks(self, L, n=1):
        """ trigger (pre and post) add, replace, and remove events n-times each on list L"""
        for i in range(n):
            L.append(i)
            L[0] = i ** 2
            L.pop()

    def test_abort_prevents_post_events_from_triggering(self):
        """ set all pre-hooks to auto-abort, and set all post-hooks to increment self.count. Verify
        that post-hooks do not run until pre-hooks don't abort
        """
        count = self.count
        premade_list = [0]  # compensate for hookup.List that prevents adding item
        for pre, post in zip(self.pre_hooks, self.post_hooks):
            hook = {pre: self.raise_abort, post: self.increment_count}
            L = hookedup.List(premade_list, **hook)
            self.trigger_all_hooks(L)
            self.assertTrue(count == self.count)
            # verify post hook would run correctly if pre hook didn't abort
            hook[pre] = lambda *_: None
            L = hookedup.List(premade_list, **hook)
            self.trigger_all_hooks(L)
            self.assertTrue(self.count == count + 1)
            count += 1

    def test_replacement_slices(self):
        """ test various slice replacement operations and verify that they match the expected
        behavior of a standard list """
        self.list = list(range(7))
        L = hookedup.List(self.list)
        self.assertTrue(type(L) == hookedup.List)
        self.assertTrue(self.list == L)
        slices = [slice(1,3), slice(1,3,2), slice(4, 0, -1)]
        replacements = [[], [-1,-2], [-3], [-4, -5, -6], [-7, -9, -9, -10, -11]]
        successes = 0
        errors = 0
        error_types_expected = (ValueError,)
        for s in slices:
            for r in replacements:
                had_error = False
                try:
                    self.list.__setitem__(s, r)
                    L.__setitem__(s, r)
                except error_types_expected as error:
                    try:
                        L.__setitem__(s, r)
                        self.fail('list, but not L accepted slice: ' + string(s) + 
                                'for replacements: ' + str(replacement))
                    except error_types_expected as error2:
                        self.assertTrue(type(error) == type(error2))
                        self.assertTrue(error.args == error2.args)
                        # verify both throw same error type and message
                    had_error = True
                finally:
                    self.assertTrue(self.list == L)
                errors += had_error
                successes += not had_error
        self.assertTrue(successes > 0 and errors > 0)








unittest.main()
