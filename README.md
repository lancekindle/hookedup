hookedup: a python library to extend the standard python list to provide callbacks before adding, removing, or replacing an item in a list.

It's very simple to use:
```
import hookedup

def hold_4_items_max(src_list, item):
	if len(src_list) == 4:
    	raise hookedup.Abort()

a = hookedup.List(range(7), pre_add=hold_4_items_max)
print(a)
>>> [0, 1, 2, 3]
```

You can execute a function for the following events: 
```
pre_add, pre_remove, pre_replace
```
```
post_add, post_remove, post_replace
```

with pre_* functions, you can raise hookedup.Abort to silently skip the operation, therefore preventing the list from changing.
All standard list operations are supported:
```
list.append, list.extend, list[0] = 3, list[2:5] = [4,-1], etc...
```

But a better use of hookedup.List is for supporting membership:
```
class Member:
	membership = None

    def __init__(self, number):
    	self.number = number

    def __str__(self):
		return str(self.number)

    @classmethod
	def list_removes_me(cls, removing_list, self):
    	if not isinstance(self, cls):
        	return  # user is removing a non-Member from list. Ignore.
        self.membership = None

    @classmethod
    def list_adds_me(cls, adding_list, self):
    	if not isinstance(self, cls):
        	return
        if self.membership is not None:
        	self.membership.remove(self)  # remove self from prior list
        self.membership = adding_list

callback = {'pre_add': Member.list_adds_me,
			'pre_remove': Member.list_removes_me,
            }

club1 = hookedup.List(**callback)
club2 = hookedup.List(**callback)
clubbers = [Member() for _ in range(5)]

club1.extend(clubbers)
for c in clubbers[1:3]:
	club2.append(c)

print(club1)
>>> [0, 3, 5]
print(club2)
>>> [1, 2]
```