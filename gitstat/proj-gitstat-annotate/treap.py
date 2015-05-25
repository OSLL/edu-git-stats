from random import random


class Treap:
    def __init__(self, value=0):
        self.value = value
        self.sum = value
        self.y = random()
        self.id = 1
        self.size = 1
        self.left = self.right = None

    def Normalize(self):
        self.id = self.size = 1 + Size(self.left)
        self.size += Size(self.right)
        self.sum = self.value + Sum(self.left) + Sum(self.right)


def Size(node):
    if node is None:
        return 0
    return node.size


def Sum(node):
    if node is None:
        return 0
    return node.sum

def Split(node, x):
    if node is None:
        return None, None
    if node.id <= x:
        node.right, b = Split(node.right, x - node.id)
        node.Normalize()
        return node, b
    else:
        a, node.left = Split(node.left, x)
        node.Normalize()
        return a, node


def Merge(left, right):
    if left is None:
        return right
    if right is None:
        return left
    if left.y < right.y:
        left.right = Merge(left.right, right)
        left.Normalize()
        return left
    else:
        right.left = Merge(left, right.left)
        right.Normalize()
        return right


def Build(n, value=None):
    root = None
    for i in range(1, n + 1):
        root = Merge(root, Treap(value or 0))
    return root


def Debug(root, level = 1):
    if root is None:
        return
    Debug(root.right, level + 1)
    print("!", "    " * level, "%d (id = %d size = %d)" % (root.value, root.id, root.size), sep="")
    Debug(root.left,  level + 1)


def Out(root, file=None):
    i = 1
    isEmpty = False
    while not root is None:
        v, root = Split(root, 1)
        if (v.value):
            print("%5d: %5d %s" % (i, v.value, file[i - 1] if not file is None else ""))
            isEmpty = False
        else:
            if not isEmpty:
                print("...")
            isEmpty = True
        i += 1
