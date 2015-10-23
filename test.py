import unittest
import hookedup
import random

class TestListSetup(unittest.TestCase):

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
        premade_list = [0]  # compensate for hookup.List that prevents appending item
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





unittest.main()
