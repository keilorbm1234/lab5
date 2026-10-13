"""
arboles.py
Árboles AVL y Red-Black basados en el código de referencia (semanas 11 y 12).

Cambios respecto al código de referencia (ver explicación en la conversación):
  * RBNode / AVLNode: los campos ahora están anotados para que @dataclass los reconozca.
  * Contador de rotaciones (self.rotations): +1 por cada llamada a rotate_left / rotate_right.
  * search_contando(): búsqueda idéntica a search() pero que cuenta comparaciones.
  * RBTree.delete() y _delete_fixup(): no existían; se implementan siguiendo CLRS.
  * validar() y altura(): comprobaciones de invariantes (se usan fuera de la medición).
"""
from dataclasses import dataclass
from typing import Any, Optional


# =====================================================================
#  ÁRBOL AVL
# =====================================================================
@dataclass(eq=False, slots=True)
class AVLNode:
    key: Any
    left: Optional["AVLNode"] = None
    right: Optional["AVLNode"] = None
    height: int = 1


def _height(n):
    """Returns node height (0 if None)."""
    return n.height if n else 0


def _update(n):
    """Updates the height of a node."""
    n.height = 1 + max(_height(n.left), _height(n.right))


def _balance(n):
    """Returns balance factor of a node."""
    return (_height(n.left) - _height(n.right)) if n else 0


class AVLTree:
    """AVL Tree with self-balancing insert and delete."""

    def __init__(self):
        self.root = None
        self.rotations = 0  # rotaciones simples acumuladas (una doble cuenta 2)

    # ---------- rotaciones ----------
    def rotate_left(self, z):
        self.rotations += 1
        y = z.right
        T2 = y.left
        y.left = z
        z.right = T2
        _update(z)
        _update(y)
        return y

    def rotate_right(self, z):
        self.rotations += 1
        y = z.left
        T3 = y.right
        y.right = z
        z.left = T3
        _update(z)
        _update(y)
        return y

    # ---------- búsqueda ----------
    def search(self, key):
        """Búsqueda original (sin contadores, para medir tiempo)."""
        cur = self.root
        while cur:
            if key == cur.key:
                return cur
            cur = cur.left if key < cur.key else cur.right
        return None

    def search_contando(self, key):
        """Misma lógica que search(); devuelve (nodo, comparaciones, nodos_visitados)."""
        cur = self.root
        comps = 0
        visitados = 0
        while cur:
            visitados += 1
            comps += 1                      # key == cur.key
            if key == cur.key:
                return cur, comps, visitados
            comps += 1                      # key < cur.key
            cur = cur.left if key < cur.key else cur.right
        return None, comps, visitados

    # ---------- inserción ----------
    def insert(self, key):
        self.root = self._insert(self.root, key)

    def _insert(self, node, key):
        if not node:
            return AVLNode(key)
        if key < node.key:
            node.left = self._insert(node.left, key)
        else:
            node.right = self._insert(node.right, key)
        _update(node)
        bf = _balance(node)
        if bf > 1 and key < node.left.key:
            return self.rotate_right(node)
        if bf < -1 and key > node.right.key:
            return self.rotate_left(node)
        if bf > 1 and key > node.left.key:
            node.left = self.rotate_left(node.left)
            return self.rotate_right(node)
        if bf < -1 and key < node.right.key:
            node.right = self.rotate_right(node.right)
            return self.rotate_left(node)
        return node

    # ---------- borrado ----------
    def _min_node(self, n):
        while n.left:
            n = n.left
        return n

    def delete(self, key):
        self.root = self._delete(self.root, key)

    def _delete(self, node, key):
        if not node:
            return None
        if key < node.key:
            node.left = self._delete(node.left, key)
        elif key > node.key:
            node.right = self._delete(node.right, key)
        else:
            if not node.left:
                return node.right
            if not node.right:
                return node.left
            succ = self._min_node(node.right)
            node.key = succ.key
            node.right = self._delete(node.right, succ.key)
        _update(node)
        bf = _balance(node)
        if bf > 1 and _balance(node.left) >= 0:
            return self.rotate_right(node)
        if bf > 1 and _balance(node.left) < 0:
            node.left = self.rotate_left(node.left)
            return self.rotate_right(node)
        if bf < -1 and _balance(node.right) <= 0:
            return self.rotate_left(node)
        if bf < -1 and _balance(node.right) > 0:
            node.right = self.rotate_right(node.right)
            return self.rotate_left(node)
        return node

    # ---------- utilidades (fuera de la medición) ----------
    def altura(self):
        return _height(self.root)

    def validar(self):
        """Comprueba orden BST, alturas y balance AVL. Devuelve la cantidad de nodos."""
        def rec(n, lo, hi):
            if n is None:
                return 0, 0
            assert (lo is None or n.key > lo) and (hi is None or n.key < hi), "AVL: orden BST violado"
            hl, cl = rec(n.left, lo, n.key)
            hr, cr = rec(n.right, n.key, hi)
            assert abs(hl - hr) <= 1, "AVL: factor de balance fuera de [-1, 1]"
            assert n.height == 1 + max(hl, hr), "AVL: altura almacenada incorrecta"
            return 1 + max(hl, hr), cl + cr + 1
        return rec(self.root, None, None)[1]


# =====================================================================
#  ÁRBOL ROJO-NEGRO
# =====================================================================
@dataclass(eq=False, slots=True)
class RBNode:
    key: Any
    color: str = "R"
    left: Optional["RBNode"] = None
    right: Optional["RBNode"] = None
    parent: Optional["RBNode"] = None


class RBTree:
    """Red-Black Tree following CLRS-style balancing rules."""

    def __init__(self):
        self.NIL = RBNode(key=None, color="B")
        self.root = self.NIL
        self.rotations = 0  # rotaciones acumuladas

    def _is_nil(self, x):
        return x is self.NIL

    # ---------- rotaciones ----------
    def rotate_left(self, x):
        self.rotations += 1
        y = x.right
        x.right = y.left
        if not self._is_nil(y.left):
            y.left.parent = x
        y.parent = x.parent
        if x.parent is None or x.parent is self.NIL:
            self.root = y
        elif x is x.parent.left:
            x.parent.left = y
        else:
            x.parent.right = y
        y.left = x
        x.parent = y

    def rotate_right(self, x):
        self.rotations += 1
        y = x.left
        x.left = y.right
        if not self._is_nil(y.right):
            y.right.parent = x
        y.parent = x.parent
        if x.parent is None or x.parent is self.NIL:
            self.root = y
        elif x is x.parent.right:
            x.parent.right = y
        else:
            x.parent.left = y
        y.right = x
        x.parent = y

    # ---------- búsqueda ----------
    def search(self, key):
        """Búsqueda original (sin contadores, para medir tiempo)."""
        cur = self.root
        while not self._is_nil(cur):
            if key == cur.key:
                return cur
            cur = cur.left if key < cur.key else cur.right
        return None

    def search_contando(self, key):
        """Misma lógica que search(); devuelve (nodo, comparaciones, nodos_visitados)."""
        cur = self.root
        comps = 0
        visitados = 0
        while not self._is_nil(cur):
            visitados += 1
            comps += 1                      # key == cur.key
            if key == cur.key:
                return cur, comps, visitados
            comps += 1                      # key < cur.key
            cur = cur.left if key < cur.key else cur.right
        return None, comps, visitados

    def _find(self, key):
        """Devuelve el nodo con esa llave, o NIL si no existe (usado por delete)."""
        cur = self.root
        while not self._is_nil(cur):
            if key == cur.key:
                return cur
            cur = cur.left if key < cur.key else cur.right
        return self.NIL

    # ---------- inserción ----------
    def insert(self, key):
        node = RBNode(key=key, color="R", left=self.NIL, right=self.NIL, parent=None)
        y = self.NIL
        x = self.root
        while not self._is_nil(x):
            y = x
            x = x.left if node.key < x.key else x.right
        node.parent = y if y is not self.NIL else None
        if y is self.NIL:
            self.root = node
        elif node.key < y.key:
            y.left = node
        else:
            y.right = node
        self._insert_fixup(node)

    def _insert_fixup(self, z):
        while z.parent and z.parent.color == "R":
            if z.parent is z.parent.parent.left:
                y = z.parent.parent.right
                if y and y.color == "R":
                    z.parent.color = "B"
                    y.color = "B"
                    z.parent.parent.color = "R"
                    z = z.parent.parent
                else:
                    if z is z.parent.right:
                        z = z.parent
                        self.rotate_left(z)
                    z.parent.color = "B"
                    z.parent.parent.color = "R"
                    self.rotate_right(z.parent.parent)
            else:
                y = z.parent.parent.left
                if y and y.color == "R":
                    z.parent.color = "B"
                    y.color = "B"
                    z.parent.parent.color = "R"
                    z = z.parent.parent
                else:
                    if z is z.parent.left:
                        z = z.parent
                        self.rotate_right(z)
                    z.parent.color = "B"
                    z.parent.parent.color = "R"
                    self.rotate_left(z.parent.parent)
        self.root.color = "B"

    # ---------- borrado (NUEVO, CLRS) ----------
    def _transplant(self, u, v):
        """Reemplaza el subárbol de u por el subárbol de v."""
        if u.parent is None:
            self.root = v
        elif u is u.parent.left:
            u.parent.left = v
        else:
            u.parent.right = v
        v.parent = u.parent          # CLRS permite fijar el padre de NIL temporalmente

    def _minimum(self, n):
        while not self._is_nil(n.left):
            n = n.left
        return n

    def delete(self, key):
        z = self._find(key)
        if self._is_nil(z):
            return
        y = z
        y_color = y.color
        if self._is_nil(z.left):
            x = z.right
            self._transplant(z, z.right)
        elif self._is_nil(z.right):
            x = z.left
            self._transplant(z, z.left)
        else:
            y = self._minimum(z.right)
            y_color = y.color
            x = y.right
            if y.parent is z:
                x.parent = y
            else:
                self._transplant(y, y.right)
                y.right = z.right
                y.right.parent = y
            self._transplant(z, y)
            y.left = z.left
            y.left.parent = y
            y.color = z.color
        if y_color == "B":
            self._delete_fixup(x)

    def _delete_fixup(self, x):
        while x is not self.root and x.color == "B":
            if x is x.parent.left:
                w = x.parent.right
                if w.color == "R":
                    w.color = "B"
                    x.parent.color = "R"
                    self.rotate_left(x.parent)
                    w = x.parent.right
                if w.left.color == "B" and w.right.color == "B":
                    w.color = "R"
                    x = x.parent
                else:
                    if w.right.color == "B":
                        w.left.color = "B"
                        w.color = "R"
                        self.rotate_right(w)
                        w = x.parent.right
                    w.color = x.parent.color
                    x.parent.color = "B"
                    w.right.color = "B"
                    self.rotate_left(x.parent)
                    x = self.root
            else:
                w = x.parent.left
                if w.color == "R":
                    w.color = "B"
                    x.parent.color = "R"
                    self.rotate_right(x.parent)
                    w = x.parent.left
                if w.right.color == "B" and w.left.color == "B":
                    w.color = "R"
                    x = x.parent
                else:
                    if w.left.color == "B":
                        w.right.color = "B"
                        w.color = "R"
                        self.rotate_left(w)
                        w = x.parent.left
                    w.color = x.parent.color
                    x.parent.color = "B"
                    w.left.color = "B"
                    self.rotate_right(x.parent)
                    x = self.root
        x.color = "B"

    # ---------- utilidades (fuera de la medición) ----------
    def altura(self):
        def h(n):
            return 0 if self._is_nil(n) else 1 + max(h(n.left), h(n.right))
        return h(self.root)

    def validar(self):
        """Comprueba las propiedades Red-Black y el orden BST. Devuelve la cantidad de nodos."""
        if self._is_nil(self.root):
            return 0
        assert self.root.color == "B", "RB: la raíz debe ser negra"
        assert self.root.parent is None, "RB: la raíz no debe tener padre"

        def rec(n, lo, hi):
            if self._is_nil(n):
                return 1, 0                      # altura negra del NIL = 1
            assert (lo is None or n.key > lo) and (hi is None or n.key < hi), "RB: orden BST violado"
            if n.color == "R":
                assert n.left.color == "B" and n.right.color == "B", "RB: nodo rojo con hijo rojo"
            for hijo in (n.left, n.right):
                if not self._is_nil(hijo):
                    assert hijo.parent is n, "RB: puntero parent inconsistente"
            bl, cl = rec(n.left, lo, n.key)
            br, cr = rec(n.right, n.key, hi)
            assert bl == br, "RB: alturas negras distintas"
            return bl + (1 if n.color == "B" else 0), cl + cr + 1
        return rec(self.root, None, None)[1]