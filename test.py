import unittest
import hookedup
import random


class TestList(unittest.TestCase):

    def setUp(self):
        self.count = 0
        self.post_hooks = ['post-add', 'post-replace', 'post-remove']
        self.pre_hooks = ['pre-add', 'pre-replace', 'pre-remove']
        
    def increment_count(self, *_):
        self.count += 1

    def raise_abort(self, *_):
        raise hookedup.Abort()

    def test_list_inits_with_empty_hook_or_no_hook(self):
        L = hookedup.List(hook={})
        L = hookedup.List()

    def test_list_works_with_random_valid_hooks(self):
        valid_hooks = self.post_hooks + self.pre_hooks
        count = 1
        while valid_hooks:
            hooks = {}
            hook_event = random.choice(valid_hooks)
            valid_hooks.remove(hook_event)
            hooks[hook_event] = self.increment_count
            L = hookedup.List(hook=hooks)
            self.trigger_all_hooks(L)
            self.assertTrue(count == self.count)
            count += 1

    def test_list_inits_with_supplied_items_from_iterable(self):
        iterables = [(0,1,2), range(3), [0,1,2], {x: None for x in range(3)}]
        for iterable in iterables:
            ll = hookedup.List(iterable)
            self.assertTrue(len(ll) == 3)
            self.assertTrue(ll == [0,1,2])

    def trigger_all_hooks(self, L, n=1):
        """ trigger (pre and post) add, replace, and remove events n-times each """
        for i in range(n):
            L.append(i)
            L[0] = i ** 2
            L.pop()

    def test_abort_prevents_post_events_from_triggering(self):
        count = self.count
        premade_list = [0]  # compensate for hookup.List that prevents adding item
        for pre, post in zip(self.pre_hooks, self.post_hooks):
            hook = {pre: self.raise_abort, post: self.increment_count}
            L = hookedup.List(premade_list, hook=hook)
            self.trigger_all_hooks(L)
            self.assertTrue(count == self.count)
            # verify post hook would run correctly if pre hook didn't abort
            hook[pre] = lambda *_: None
            L = hookedup.List(premade_list, hook=hook)
            self.trigger_all_hooks(L)
            self.assertTrue(self.count == count + 1)
            count += 1

    def test_replacing_with_slices(self):
        """ test various slice replacement operations and verify that they match the expected
        behavior of a standard list """
        self.list = list(range(7))
        L = hookedup.List(self.list)
        self.assertTrue(type(L) == hookedup.List)
        self.assertTrue(self.list == L)
        self.assertTrue(len(self.list) == len(L))
        slices = [slice(1,3), slice(1,3,2), slice(4, 0, -1)]
        replacements = [[-1,-2], [-3], [-4, -5, -6], [-7, -9, -9, -10, -11], []]
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
