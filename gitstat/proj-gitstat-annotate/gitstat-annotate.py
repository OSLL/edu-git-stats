#!/usr/bin/python3

from random import random

class Treap:
    def __init__(self, value):
        self.value = value
        self.y = random()
        self.cnt = 0
        self.toAdd = 0
        self.left = self.right = None

    def Push(self):
        if not self.left is None:
            self.left.toAdd += self.toAdd
        if not self.right is None:
            self.right.toAdd += self.toAdd
        self.cnt += self.toAdd
        self.toAdd = 0

def Split(node, x):
    if node is None:
        return None, None
    node.Push()
    if node.x <= x:
        node.right, b = Split(node.right, x)
        return node, b
    else:
        a, node.left = Split(node.left, x)
        return a, node

def Merge(left, right):
    if left is None:
        return right
    if right is None:
        return left
    if left.y < right.y:
        left.right = Merge(left.right, right)
        return left
    else:
        right.left = Merge(left, right.left)
        return right

def Build(n):
    root = None
    for i in range(1, n + 1):
        Merge(root, Treap(i))
    return root

def Out(root):
    i = 1
    while not root is None:
        v, root = Split(root, i)
        i += 1
        print("%d: %d" % (i, v.cnt))
    

