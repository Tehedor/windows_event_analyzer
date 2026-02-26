Tipos de consulta
## Consultas Lógicas
### Nivel 0 -> Concatenación secuencial `,`
El operador `,` representa concatenación ordenada de elementos o expresiones.
```python
src = "475,511"
# Coincide únicamente con la secuencia exacta [475,511]

src = "(475 | 511),452"
# Coincide con:
# 475,452
# 511,452
```

### Nivel 1 -> Atómicas
#### Comodín único `?` 
Representa **exactamente un elemento** en una posición concreta.
```python
src = "475,?,511"
# Coincide con:
# 475,123,511
# 475,999,511
# NO coincide con:
# 475,511
# 475,12,13,511       
```


#### Comodín de grupo `*`
Representa **una secuencia de longitud variable** (≥ 0).
```python
src = "475,*,511"
# Coincide con:
# 475,511
# 475,12,511
# 475,12,13,14,511
```

```python
src = "475,*"
# Coincide con cualquier secuencia que EMPIECE por 475
# 475
# 475,12
# 475,12,13,...
```


### Nivel 2 -> Grupo
Permiten **composición semántica**, sin añadir nuevos inputs al frontend.
#### Grupo Lógico `()`
Agrupan expresiones para controlar la evaluación lógica.
``` python
src = "(475,* | 511,*) & ?,612"
# Coincide con secuencias que:
# - empiecen por 475 O por 511
# - Y además terminen en 612
```
Los paréntesis no alteran el patrón, solo la lógica

#### Pertenencia `{}`
Comprueba si una secuencia contiene uno o más elementos independientemente de la posición.
```python
src = "{511}"
# Coincide con cualquier secuencia que CONTENGA el valor 511
# Ej:
# 511
# 475,511
# 475,12,511,14
```

```python
src = "{12 | 13}"
# Coincide con secuencias que contengan 12 O 13
```

```python
src = "475,* & {511}"
# Empieza por 475
# Y en algún punto contiene el valor 511

```

> `{}` **no define orden**, solo pertenencia.
> `{}` no puede usarse como elemento secuencial directo.
> Solo es válido dentro de expresiones lógicas (`&`, `|`, `!`).

### Nivel 3 -> Lógicas
Los operadores lógicos **siempre actúan entre expresiones completas**  
(no entre números individuales).
#### 1. OR lógico `|`
Une resultados de varias expresiones.
- **OR atómico**
```python
src = "(484 | 511)"
# Coincide con:
# [484]
# [511]
```
- **OR de patrones completos**
```python
src = "475,484,* | 511,612,*"
# Coincide con:
# - secuencias que empiezan por 475,484
# - O secuencias que empiezan por 511,612
```
- **OR mixto**
```python
src = "(475,484,* | 511),452"
# Coincide con:
# 475,484,...,452
# 511,452
```




#### 2. AND lógico `&`
Aplica **múltiples restricciones simultáneas** sobre la misma secuencia.

- **AND de patrones**
```python
src = "475,484,* & *,511"
# Coincide con secuencias que:
# - empiezan por 475,484
# - Y terminan en 511
           # Empiece por 475, 484 y termine por 511
```

- **AND con pertenencia**
```python
src = "475,484,* & {511}"
# Coincide con secuencias que:
# - empiezan por 475,484
# - Y contienen el valor 511 en cualquier posición
```
> El AND **reduce** el conjunto de resultados.

#### 3. Negación  `!`
 Excluye patrones o condiciones.
-  **Negación atómica posicional**
```python
src = "!13,14"
# Secuencias donde:
# - el primer elemento NO es 13
# - el segundo elemento ES 14

```

```python
src = "!13,*"
# Secuencia cuyo PRIMER elemento no es 13
# [13,*]
```

- **Negación de patrón**
```python
src = "!(475,484,*)"
# Coincide con todas las secuencias
# EXCEPTO las que empiezan por 475,484
```
- **Negación combinada**
```python
src = "475,* & !{511}"
# Empieza por 475
# Y NO contiene el valor 511
```


## Consultas de componente. Alias semánticos
Componentes Actuales:
```yml
# Datasets/Dataset_ventanas/components.yml
components:
  Battery_Active_Power:
    color: "#FF0000"
    description: "Battery active power"
  Battery_Active_Power_Set_Response:
    color: "#CC0000"
    description: "Battery active power set response"
  PVPCS_Active_Power:
    color: "#00FF00"
    description: "PVPCS active power"
  GE_Body_Active_Power:
    color: "#0000FF"
    description: "GE Body active power"
    metrics:
  GE_Active_Power:
    color: "#FFA500"
    description: "GE active power"
  GE_Body_Active_Power_Set_Response:
    color: "#FF8C00"
    description: "GE Body active power set response"
  FC_Active_Power_FC_END_Set:
    color: "#800080"
    description: "FC END set active power"
  FC_Active_Power:
    color: "#9932CC"
    description: "FC active power"
  FC_Active_Power_FC_end_Set_Response:
    color: "#BA55D3"
    description: "FC end set response active power"
  Island_mode_MCCB_Active_Power:
    color: "#008080"
    description: "Island mode MCCB active power"
  MG-LV-MSB_AC_Voltage:
    color: "#A52A2A"
    description: "MG-LV-MSB AC voltage"
  Receiving_Point_AC_Voltage:
    color: "#2F4F4F"
    description: "Receiving Point AC voltage"
  Island_mode_MCCB_AC_Voltage:
    color: "#556B2F"
    description: "Island mode MCCB AC voltage"
  Island_mode_MCCB_Frequency:
    color: "#4682B4"
    description: "Island mode MCCB frequency"
  MG-LV-MSB_Frequency:
    color: "#B22222"
    description: "MG-LV-MSB frequency"
  Inlet_Temperature_of_Chilled_Water:
    color: "#FF1493"
    description: "Inlet temperature of chilled water"
  Outlet_Temperature:
    color: "#1E90FF"
    description: "Outlet temperature"
```

```python
src = `"@Outlet_Temperature | @MG-LV-MSB_Frequency"
```
Donde estos dos estarían compuesto estos elementos (no real)
``` yml
MG-LV-MSB_Frequency:
  - 475
  - 612
Outlet_Temperature:
  - 511
```

Equivale a:
```python
(475 | 612) | (511)
```


---

# Normalización Nombre Output file.
## Nivel 0
### Numérico
```python
475           → 475
```
Ej:
``` python
src = "475"
→ src_475
```

### Concatenación Secuencial `,`
```python
, → -
```
Ej:
``` python
src = "475,484,511"
→ src_475-484-511
```



## Nivel 1 Patrones atómicos
### Comodín único `?`
``` python
? → any
```
Ej:
```python
src = "475,?,511"
→ src_475-any-511
```

### Comodín de grupo `*`
``` python
* → star
```
Ej:
``` python
src = "475,*"
→ src_475-star
```


## Nivel 2 Grupo
### Grupo Lógico `()`
Los paréntesis `()` no se representan en los nombres de fichero.

>Durante la normalización:
>- Las expresiones se reducen a su forma lógica equivalente.
>- Los operadores `or`, `and`, `not` reflejan completamente la semántica.
>- El nombre final es independiente del árbol de agrupación original.



### Pertenencia `{}`
No importa el orden, solo que esté

```python
{X} → has-X
```

- Pertenencia Simple
```python
src = "{511}"
→ src_has-511
```

- Pertenencia OR
```python
src = "{12 | 13}"
→ src_has-12-or-13
```

## Nivel 3 Lógicas
### OR lógico `|`


``` python
| → or
```

```python
src = "475 | 511"
→ src_475-or-511
```

### AND lógico `&`
``` python
& → and
```

```python
src = "475,484,* & *,511"
→ src_475-484-star-and-star-511
```



### Negación `!`

```python
! → not
```

1. Negación de patrón
```python
src = "!(475,484,*)"
```

```python
src_not-475-484-star
```


2. Negación combinada
```python
src = "475,* & !{511}"
src_475-star-and-not-has-511
```




## Alias semánticos
Los alias No deben aparecer en el filename final, siempre se expanden a su forma numérica

```yaml
Outlet_Temperature → 511
MG-LV-MSB_Frequency → 475 | 612
```



```python
src = "@Outlet_Temperature | @MG-LV-MSB_Frequency"
→ src_511-or-475-or-612
```

