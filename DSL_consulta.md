### Tabla de Tipos de Inputs y Operadores

| Categoría | Sintaxis / Operador | Descripción |
| --- | --- | --- |
| **Coincidencia Exacta** | `Valor` o `V1, V2` | Busca un evento único (`475`) o una secuencia estricta (`475,511`). |
| **Comodín Múltiple** | `*` | Representa cero, uno o múltiples eventos (ej. `475,*` empieza por 475). |
| **Comodín Único** | `?` | Representa exactamente **un** evento cualquiera (ej. `475,?,511`). |
| **Pertenencia (Contiene)** | `{Valor}` | Obliga a que la secuencia contenga el evento en cualquier posición. |
| **Negación (NO Contiene)** | `!{Valor}` | Excluye secuencias que contengan el evento. |
| **Lógica Booleana** | ` \| `(OR) ,`&` (AND) |
| **Agrupación** | `(...)` | Agrupa secuencias lógicas para aislar condiciones (ej. `({A} |
| **Alias de Componente** | `@NombreAlias` | Llama a variables configuradas previamente (ej. `@Outlet_Temperature`). |
| **Entornos** | `src:` y `dst:` | `src` aplica al origen/observación. `dst` aplica a la predicción/destino. El valor `null` ignora el campo. |

---

### Ejemplos Prácticos de Uso

**1. Búsquedas Secuenciales y Patrones**

* **Empieza por:** `src: "475,*"` (Empieza en 475, sigue cualquier cosa).
* **Termina en:** `src: "*,511"` (Cualquier cosa antes, termina en 511).
* **Patrón con salto temporal:** `src: "49, ?, 148,*"` (Empieza en 49, un evento X, luego 148 y cualquier cosa).

**2. Búsquedas por Pertenencia y Negación**

* **Contiene 511:** `src: "{511}"`
* **NO contiene 511:** `src: "!{511}"`
* **Interacción compleja AND + Negación:** `dst: "{143} & !{24}"` (Debe contener 143 y NO contener 24).

**3. Lógica Booleana y Agrupaciones**

* **OR Secuencial:** `src: "(49,143, 148,*) | (143,148,143,*)"` (Cumple la secuencia A o la secuencia B).
* **AND con subgrupos:** `src: "(49,143, 148,*) & ({49} | !{13})"` (Cumple la secuencia Y ADEMÁS debe contener 49 o no contener 13).

**4. Uso de Alias**

* **Alias directo:** `src: "@Outlet_Temperature"`
* **Alias con comodines e inserción:** `src: "*,(@Outlet_Temperature | @Battery_Active_Power),*"` (Contiene uno de los dos alias en algún punto de la secuencia).

**5. Interacción Origen (SRC) vs Destino (DST)**

* **Filtro mixto:** * `src: "475,*"` (El origen empieza por 475).
* `dst: "{511}"` (Y el destino asociado debe contener 511).


* **Solo buscar por destino:** * `src: null`
* `dst: "*,612"` (Trae todas las secuencias cuyo destino termine en 612).

