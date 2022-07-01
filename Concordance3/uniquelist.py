class UniqueList(list):
    def add(self, items):
        if type(items) != list:
            items = [items]
        for item in items:
            if item not in self:
                self.append(item)