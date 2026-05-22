#set page(margin: 2.2cm)
#set text(size: 11pt)
#set math.equation(numbering: none)

#align(center)[
  #text(size: 18pt, weight: "bold")[
    Resolución de la ecuación $2^x = 3x + 4$
    mediante la función de Lambert $W$
  ]
]

#v(0.8em)

= Planteamiento

Queremos resolver la ecuación
$
  2^x = 3x + 4
$
y mostrar que tiene dos soluciones reales usando la función de Lambert $W$.
Además, aproximaremos las raíces mediante el método de Newton.

= Transformación a la forma de Lambert

Escribimos la potencia en forma exponencial:
$
  2^x = e^(x ln 2)
$
Entonces la ecuación queda
$
  e^(x ln 2) = 3x + 4
$
Hacemos el cambio de variable
$
  y = 3x + 4, quad x = frac(y - 4, 3)
$
Sustituyendo:
$
  e^(frac((y - 4) ln 2, 3)) = y
$
Multiplicamos ambos lados por $e^(-frac(ln 2, 3) y)$ para obtener
$
  y e^(-frac(ln 2, 3) y) = 2^(-4/3)
$
Multiplicamos por $-frac(ln 2, 3)$ y definimos $u = -frac(ln 2, 3) y$. Entonces:
$
  u e^u = -frac(ln 2, 3) dot 2^(-4/3)
$
Definimos
$
  z = -frac(ln 2, 3) dot 2^(-4/3)
$
y por definición de la función de Lambert,
$
  u = W_k (z)
$
Por tanto, $-frac(ln 2, 3) y = W_k (z)$, de donde
$
  y = -frac(3, ln 2) W_k (z)
$
Como $y = 3x + 4$, tenemos $3x + 4 = -frac(3, ln 2) W_k (z)$, y finalmente
$
  x = -frac(1, ln 2) W_k (z) - frac(4, 3)
$
Así, la solución general es:
$
  x = -frac(1, ln 2) W_k lr((-frac(ln 2, 3) dot 2^(-4/3))) - frac(4, 3)
$

= Número de soluciones reales

El argumento de Lambert es
$
  z = -frac(ln 2, 3) dot 2^(-4/3) approx -0.09169
$
Sabemos que la función $W$ tiene dos ramas reales cuando $-1/e <= z < 0$.
Como $-1/e approx -0.36788$ y $-0.36788 < -0.09169 < 0$, existen exactamente
dos ramas reales:
$
  W_0 (z) quad "y" quad W_(-1) (z)
$
Por lo tanto, la ecuación tiene exactamente *dos soluciones reales*.

= Soluciones aproximadas

Usando las dos ramas:
$
  x_1 = -frac(1, ln 2) W_0 (z) - frac(4, 3) approx -1.186920152
$
$
  x_2 = -frac(1, ln 2) W_(-1) (z) - frac(4, 3) = 4
$
*Verificación de $x_2 = 4$:*
$
  2^4 = 16 quad "y" quad 3(4) + 4 = 16 checkmark
$
Por tanto $x = 4$ es una solución exacta, y la otra es $x approx -1.186920152$.

= Método de Newton

Definimos $f(x) = 2^x - 3x - 4$ con derivada $f'(x) = ln(2) dot 2^x - 3$.
La iteración de Newton es:
$
  x_(n+1) = x_n - frac(2^(x_n) - 3 x_n - 4, ln(2) dot 2^(x_n) - 3)
$

== Convergencia numérica

Las siguientes tablas muestran la rápida convergencia del método hacia cada raíz.

#v(0.6em)

#grid(
  columns: (1fr, 1fr),
  gutter: 2em,
  [
    *Raíz negativa* ($x_0 = -1$)

    #table(
      columns: (auto, 1fr, 1fr),
      align: (center, right, right),
      stroke: 0.4pt + luma(180),
      inset: (x: 8pt, y: 5pt),
      fill: (_, row) => if row == 0 { luma(230) } else if calc.even(row) { luma(248) },
      table.header[$n$][$x_n$][$f(x_n)$],
      [0], [-1.000 000 000], [$-5.000 times 10^(-1)$],
      [1], [-1.188 435 601], [$4.085 times 10^(-3)$],
      [2], [-1.186 920 242], [$2.421 times 10^(-7)$],
      [3], [-1.186 920 152], [$approx 0$],
    )
  ],
  [
    *Raíz positiva* ($x_0 = 5$)

    #table(
      columns: (auto, 1fr, 1fr),
      align: (center, right, right),
      stroke: 0.4pt + luma(180),
      inset: (x: 8pt, y: 5pt),
      fill: (_, row) => if row == 0 { luma(230) } else if calc.even(row) { luma(248) },
      table.header[$n$][$x_n$][$f(x_n)$],
      [0], [5.000 000 000], [$1.300 times 10^1$],
      [1], [4.322 235 718], [$3.038$],
      [2], [4.042 686 128], [$3.524 times 10^(-1)$],
      [3], [4.000 848 016], [$6.864 times 10^(-3)$],
      [4], [4.000 000 342], [$2.763 times 10^(-6)$],
      [5], [4.000 000 000], [$approx 0$],
    )
  ]
)

#v(0.8em)

== Código en Python

```python
import math

def f(x):
    return 2**x - 3*x - 4

def df(x):
    return math.log(2) * 2**x - 3

def newton(x0, tol=1e-12, max_iter=100):
    x = x0
    for n in range(max_iter):
        x_next = x - f(x) / df(x)
        if abs(x_next - x) < tol:
            return x_next, n + 1
        x = x_next
    return x, max_iter

raiz1, iter1 = newton(-1)
raiz2, iter2 = newton(5)

print("Raiz negativa:", raiz1)   # -1.186920152081...
print("Iteraciones:",  iter1)    # 3
print("Raiz positiva:", raiz2)   # 4.0
print("Iteraciones:",  iter2)    # 5
```

= Conclusión

La ecuación $2^x = 3x + 4$ se expresa mediante la función de Lambert como
$
  x = -frac(1, ln 2) W_k lr((-frac(ln 2, 3) dot 2^(-4/3))) - frac(4, 3)
$
Como el argumento $z approx -0.09169$ pertenece al intervalo $[-1/e,, 0)$, existen
dos ramas reales de $W$, dando exactamente dos soluciones reales:
$
  x_1 approx -1.186920152 quad "y" quad x_2 = 4
$
El método de Newton confirma ambas soluciones con convergencia cuadrática
en pocos pasos.
