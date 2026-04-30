"""Docstring for utils.geometry.

Docstring.
"""
def area(bbox):
    # Calcula el área del bounding box.
    x0,y0,x1,y1 = bbox
    # Evitar areas negativas si el bbox esta mal definido
    return max(0, x1-x0) * max(0, y1-y0)

def intersection(a,b):
    # Calcula el área de intersección entre dos bounding boxes.
    x0 = max(a[0], b[0])
    y0 = max(a[1], b[1])
    x1 = min(a[2], b[2])
    y1 = min(a[3], b[3])
    # Si no se solapan, retorna 0
    if x1 <= x0 or y1 <= y0:
        return 0
    # Si se solapan, retorna área en común
    return (x1-x0)*(y1-y0)

def iou_bbox(a,b):
    # Calcula el IoU (Intersection over Union):
    # IoU = Area_intersection / Area_union. 
    inter = intersection(a,b)
    union = area(a) + area(b) - inter
    # Un valor entre 0 y 1, 0 si no se solapan, 1 si son iguales
    return (
        inter/union
        if union > 0
        else 0
    )

def overlaps(a,b,threshold=0.1):
    # Devuelve True / False según si dos cajas se consideran solapadas.
    return iou_bbox(a,b) > threshold