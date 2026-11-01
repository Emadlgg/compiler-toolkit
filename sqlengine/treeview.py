"""
treeview.py — Representación genérica de un árbol para mostrarlo.

Tanto el árbol sintáctico como el AST se convierten a este formato, y de ahí salen
las dos vistas: el texto con sangría (línea de comandos) y el dibujo (interfaz gráfica).
"""


class TreeItem:
    """Un nodo para mostrar: su texto, su tipo (para darle estilo) y sus hijos."""

    # kind: "node"  regla o nodo con hijos
    #       "leaf"  hoja (token, literal, columna...)
    #       "role"  título que agrupa hijos ("where:", "items:"...); no es un nodo del árbol
    def __init__(self, label, kind="node", children=None):
        self.label = label
        self.kind = kind
        self.children = children if children is not None else []

    def __repr__(self):
        return f"TreeItem({self.label!r}, {self.kind!r}, {len(self.children)} hijos)"


def render_text(item, indent=0):
    """El árbol como texto, con dos espacios de sangría por nivel."""
    lines = []

    def walk(node, depth):
        lines.append("  " * depth + node.label)
        for child in node.children:
            walk(child, depth + 1)

    walk(item, indent)
    return "\n".join(lines)


def count(item):
    """Cantidad de nodos del árbol."""
    return 1 + sum(count(c) for c in item.children)
