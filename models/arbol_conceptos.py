from models.base_model import BC3BaseModel
from models.medicion import Medicion
from models.concepto import Concepto

from typing import Optional, List, Dict, Any
from decimal import Decimal
from pydantic import Field


class NodoConcepto(BC3BaseModel):
    """Nodo del arbol de conceptos"""

    concepto: Concepto = Field(
        ...,
        description="Datos del concepto asociado (~C)"
    )

    codigo_padre: Optional[str] = Field(
        None,
        description="Código del concepto padre o None para el nodo raíz"
    )

    codigos_hijos: List[str] = Field(
        default_factory=list,
        description="Lista con los códigos de los conceptos hijos"
    )

    nivel_jerarquico: int = Field(
        0,
        description="Nivel en el árbol (0 = raíz)"
    )

    ruta_completa: List[str] = Field(
        default_factory=list,
        description="Ruta desde la raíz hasta este nodo"
    )

    mediciones: List[Medicion] = Field(
        default_factory=list,
        description="Mediciones asociadas a este concepto"
    )

    # ----- Propiedades derivadas -----
    tiene_hijos: bool = Field(
        False,
        description="Indica si el concepto tiene hijos"
    )

    numero_hijos: int = Field(
        0,
        description="Indica el número de hijos directos"
    )

    numero_mediciones: int = Field(
        0,
        description="Indica el número de mediciones asociadas"
    )

    importe_propio: Optional[Decimal] = Field(
        None,
        description="Importe del concepto sin incluir hijos"
    )

    importe_total_arbol: Optional[Decimal] = Field(
        0,
        description="Importe total incluyendo el importe de los hijos"
    )

    medicion_total: Optional[Decimal] = Field(
        None,
        description="Total de mediciones para este concepto"
    )

    def calcular_propiedades(self):
        """Calcula las propiedades derivadas del nodo"""
        self.numero_hijos = len(self.codigos_hijos)
        self.tiene_hijos = self.numero_hijos > 0
        self.numero_mediciones = len(self.mediciones)
        self.importe_propio = self.concepto.precio

        # Calcular el total de mediciones
        if self.mediciones:
            total = Decimal('0')
            for med in self.mediciones:
                if med.medicion_total:
                    total += med.medicion_total
            self.medicion_total = total

    def agregar_hijo(
        self,
        codigo_hijo: str
    ):
        """Agrega un hijo al nodo"""
        if codigo_hijo not in self.codigos_hijos:
            self.codigos_hijos.append(codigo_hijo)
            self.calcular_propiedades()

    def agregar_medicion(
        self,
        medicion: Medicion
    ):
        """Agrega una medición al nodo"""
        self.mediciones.append(medicion)
        self.calcular_propiedades()

    def es_raiz(self) -> bool:
        """Verifica si es el nodo raiz"""
        return self.codigo_padre is None

    def es_hoja(self) -> bool:
        """Verifica si el nodo no tiene hijos"""
        return not self.tiene_hijos

    def get_path_string(
        self,
        separator: str = " > "
    ) -> str:
        """Obtiene la ruta del nodo como un string"""
        if not self.ruta_completa:
            return self.concepto.codigo

        return separator.join(self.ruta_completa + [self.concepto.codigo])


class ArbolConceptos(BC3BaseModel):
    """Árbol completo de conceptos del BC3"""

    nodos: Dict[str, NodoConcepto] = Field(
        default_factory=dict,
        description="Diccionario de los nodos indexados por su código"
    )

    nodos_raiz: List[str] = Field(
        default_factory=list,
        description="Lista de códigos de nodos raíz (usualmente solo 1)"
    )

    nodos_por_nivel: Dict[int, List[str]] = Field(
        default_factory=dict,
        description="Npodos agrupados por nivel jerarquico (0 = raiz)"
    )

    # ----- Propiedades derivadas -----
    total_nodos: int = Field(
        0,
        description="Total de nodos en un árbol"
    )

    niveles_maximos: int = Field(
        0,
        description="Número de niveles en un árbol"
    )

    importe_total_presupuesto: Optional[Decimal] = Field(
        0,
        description="Importe total de todo el presupuesto"
    )

    # Agregar campo archivo_origen
    archivo_origen: Optional[str] = Field(
        None,
        description="Archivo BC3 de origen"
    )

    def agregar_nodo(
        self,
        nodo: NodoConcepto
    ):
        """Agrega un nodo al árbol"""
        self.nodos[nodo.concepto.codigo] = nodo

        if nodo.es_raiz():
            if nodo.concepto.codigo not in self.nodos_raiz:
                self.nodos_raiz.append(nodo.concepto.codigo)

        nivel = nodo.nivel_jerarquico
        if nivel not in self.nodos_por_nivel:
            self.nodos_por_nivel[nivel] = []

        if nodo.concepto.codigo not in self.nodos_por_nivel[nivel]:
            self.nodos_por_nivel[nivel].append(nodo.concepto.codigo)

        self.calcular_estadisticas()

    def establecer_relacion_padre_hijo(  # CORREGIDO: nombre del método
        self,
        codigo_padre: str,
        codigo_hijo: str
    ):
        """Establece una relación padre-hijo entre dos nodos"""
        if codigo_padre in self.nodos and codigo_hijo in self.nodos:
            # Evitar relaciones circulares
            if codigo_hijo == codigo_padre:
                return False

            # Evitar que un nodo sea padre de su propio ancestro
            hijo = self.nodos[codigo_hijo]
            if hijo.codigo_padre and self._es_ancestro(
                    codigo_hijo, codigo_padre):
                return False

            self.nodos[codigo_padre].agregar_hijo(codigo_hijo)

            hijo.codigo_padre = codigo_padre

            padre = self.nodos[codigo_padre]
            hijo.nivel_jerarquico = padre.nivel_jerarquico + 1
            hijo.ruta_completa = padre.ruta_completa + [codigo_padre]

            self._actualizar_indices_nodo(hijo)
            return True
        return False

    def _es_ancestro(self, posible_ancestro: str, nodo: str) -> bool:
        """Verifica si un nodo es ancestro de otro (para evitar ciclos)"""
        actual = nodo
        while actual in self.nodos:
            nodo_actual = self.nodos[actual]
            if nodo_actual.codigo_padre == posible_ancestro:
                return True
            actual = nodo_actual.codigo_padre
            if not actual:
                break
        return False

    def agregar_medicion_a_concepto(
        self,
        codigo_concepto: str,
        medicion: Medicion
    ):
        """Agrega una medición a un concepto especifico"""
        if codigo_concepto in self.nodos:
            self.nodos[codigo_concepto].agregar_medicion(medicion)

    def obtener_hijos_directos(
        self,
        codigo_padre: str
    ) -> List[NodoConcepto]:
        """Obtiene los hijos directos de un nodo"""
        if codigo_padre not in self.nodos:
            return []

        nodo_padre = self.nodos[codigo_padre]
        return [self.nodos[codigo] for codigo in nodo_padre.codigos_hijos
                if codigo in self.nodos]

    # TODO: Estudiar la posibiolidad de no recursividad
    def obtener_todos_descendientes(
        self,
        codigo_padre: str
    ) -> List[NodoConcepto]:
        """Obtiene todos los descendientyes de un nodo"""
        descendientes = []

        if codigo_padre not in self.nodos:
            return descendientes

        directos = self.obtener_hijos_directos(codigo_padre)
        descendientes.extend(directos)

        for hijo in directos:
            descendientes.extend(
                self.obtener_todos_descendientes(hijo.concepto.codigo))
        return descendientes

    def obtener_ruta_hasta_raiz(
        self,
        codigo: str
    ) -> List[NodoConcepto]:
        """Obtiene la ruta de un nodo hasta su raíz"""
        ruta = []

        if codigo not in self.nodos:
            return ruta

        nodo = self.nodos[codigo]
        ruta.append(nodo)

        while nodo.codigo_padre:
            nodo = self.nodos[nodo.codigo_padre]
            ruta.append(nodo)

        return list(reversed(ruta))  # CORREGIDO: era list.reverse(ruta)

    def calcular_importes_arbol(self):
        """Calcula importes totales considerando la estructura del árbol"""
        # Calcular de hojas hacia raíz
        for nivel in reversed(range(self.niveles_maximos + 1)):
            if nivel in self.nodos_por_nivel:
                for codigo in self.nodos_por_nivel[nivel]:
                    self._calcular_importe_nodo(codigo)

        # Calcular importe total del presupuesto
        total_presupuesto = Decimal('0')
        for codigo_raiz in self.nodos_raiz:
            nodo_raiz = self.nodos[codigo_raiz]
            if nodo_raiz.importe_total_arbol:
                total_presupuesto += nodo_raiz.importe_total_arbol

        self.importe_total_presupuesto = total_presupuesto

    def obtener_estructura_json(
        self
    ) -> Dict[str, Any]:
        """Convierte el árbol a una estructura JSON anidada"""
        def _nodo_a_dict(nodo: NodoConcepto) -> Dict[str, Any]:
            hijos = []
            for codigo_hijo in nodo.codigos_hijos:
                if codigo_hijo in self.nodos:
                    hijos.append(_nodo_a_dict(self.nodos[codigo_hijo]))

            return {
                'codigo': nodo.concepto.codigo,
                'resumen': nodo.concepto.resumen,
                'unidad': nodo.concepto.unidad,
                'precio': (float(nodo.concepto.precio)
                           if nodo.concepto.precio else None),
                'nivel': nodo.nivel_jerarquico,
                'tipo': nodo.concepto.tipo,
                'es_capitulo': nodo.concepto.es_capitulo,
                'es_partida': nodo.concepto.es_partida,
                'numero_hijos': nodo.numero_hijos,
                'numero_mediciones': nodo.numero_mediciones,
                'medicion_total': (float(nodo.medicion_total)
                                   if nodo.medicion_total else None),
                'importe_propio': (float(nodo.importe_propio)
                                   if nodo.importe_propio else None),
                'importe_total_arbol': (float(nodo.importe_total_arbol)
                                        if nodo.importe_total_arbol else None),
                'ruta': nodo.get_path_string(),
                'mediciones': [med.dict() for med in nodo.mediciones],
                'hijos': hijos
            }

        estructura = {
            'metadata': {
                'total_nodos': self.total_nodos,
                'niveles_maximos': self.niveles_maximos,
                'importe_total_presupuesto': (
                    float(self.importe_total_presupuesto)
                    if self.importe_total_presupuesto else None)
            },
            'arbol': []
        }

        # Construir árbol desde las raíces
        for codigo_raiz in self.nodos_raiz:
            if codigo_raiz in self.nodos:
                estructura['arbol'].append(
                    _nodo_a_dict(self.nodos[codigo_raiz]))

        return estructura

    def calcular_estadisticas(self):
        """Calcula estadísticas del árbol"""
        self.total_nodos = len(self.nodos)
        self.niveles_maximos = max(
            self.nodos_por_nivel.keys()) if self.nodos_por_nivel else 0

    def _actualizar_indices_nodo(
        self,
        nodo: NodoConcepto
    ):
        """Actualiza los índices cuando se modifica un nodo"""
        nivel = nodo.nivel_jerarquico

        if nivel not in self.nodos_por_nivel:
            self.nodos_por_nivel[nivel] = []

        if nodo.concepto.codigo not in self.nodos_por_nivel[nivel]:
            self.nodos_por_nivel[nivel].append(nodo.concepto.codigo)

        self.calcular_estadisticas()

    def _calcular_importe_nodo(
        self,
        codigo: str
    ):
        """Calcula el importe total de un nodo incluyendo sus descendientes"""
        if codigo not in self.nodos:
            return

        nodo = self.nodos[codigo]

        # Importe propio
        importe_total = nodo.importe_propio or Decimal('0')

        # Sumar importes de hijos directos
        for codigo_hijo in nodo.codigos_hijos:
            if codigo_hijo in self.nodos:
                hijo = self.nodos[codigo_hijo]
                if hijo.importe_total_arbol:
                    importe_total += hijo.importe_total_arbol

        nodo.importe_total_arbol = importe_total
