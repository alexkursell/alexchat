class AddressBook(dict):
    '''
    A bi-directional dictionary (hash table) used to store username:ip pairs
    and have them be referencable quickly either way. Written by Basj and found
    on StackOverflow at http://stackoverflow.com/a/21894086.
    Modified slightly to improve naming for this particular usage.
    '''
    def __init__(self, *args, **kwargs):
        super(__class__, self).__init__(*args, **kwargs)
        self.byName = {}
        for key, value in self.items():
            self.byName.setdefault(value,[]).append(key) 

    def __setitem__(self, key, value):
        super(__class__, self).__setitem__(key, value)
        self.byName.setdefault(value,[]).append(key)        

    def __delitem__(self, key):
        self.byName.setdefault(self[key],[]).remove(key)
        if self[key] in self.byName and not self.byName[self[key]]: 
            del self.byName[self[key]]
        super(__class__, self).__delitem__(key)


if __name__ == "__main__":
    a = AddressBook()
    a["a"] = 1
    print("a" in a.byName)
    print(a["a"], a.byName[1])