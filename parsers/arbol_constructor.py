from models.arbol_conceptos import ArbolConceptos, NodoConcepto
from models.descomposicion import Descomposicion
from models.medicion import Medicion
from models.concepto import Concepto

from typing import Dict, Set, List
from collections import defaultdict, deque

import logging

logger = logging.getLogger(__name__)


class ArbolConstructor:
    """Construye el árbol de conceptos"""

    def __init__(self):
        self.arbol = ArbolConceptos()
        self.relaciones_padre_hijo: Dict[str, Set[str]] = defaultdict(set)
        self.mediciones_por_concepto: Dict[str,
                                           List[Medicion]] = defaultdict(list)

    def construir_arbol(
        self,
        conceptos: List[Concepto],
        descomposiciones: List[Descomposicion],
        mediciones: List[Medicion]
    ) -> ArbolConceptos:
        """
        Construye el árbol completo de conceptos con asociación
        mejorada de mediciones

        Args:
            conceptos: Lista de conceptos
            descomposiciones: Lista de descomposiciones
            mediciones: Lista de mediciones

        Returns:
            Árbol completo de conceptos
        """
        logger.info("Construyendo árbol de conceptos...")

        # Reinicializar el árbol para cada construcción
        self.arbol = ArbolConceptos()
        self.relaciones_padre_hijo = defaultdict(set)
        self.mediciones_por_concepto = defaultdict(list)

        self._crear_nodos(conceptos)
        self._procesar_descomposiciones(descomposiciones)
        self._detectar_jerarquia_por_codigo(conceptos)
        self._construir_estructura_final()
        self._asociar_mediciones(mediciones)
        self.arbol.calcular_importes_arbol()

        logger.info(f"Árbol construido: {self.arbol.total_nodos} nodos, "
                    f"{len(self.arbol.nodos_raiz)} raíces, "
                    f"{self.arbol.niveles_maximos + 1} niveles")

        return self.arbol

    def obtener_estadisticas_construccion(
        self
    ) -> Dict[str, int]:
        """Obtiene estadísticas del proceso de construcción"""
        stats = {
            'total_nodos': len(self.arbol.nodos),
            'nodos_raiz': len(self.arbol.nodos_raiz),
            'relaciones_padre_hijo': sum(
                len(hijos) for hijos
                in self.relaciones_padre_hijo.values()
            ),
            'niveles_maximos': self.arbol.niveles_maximos,
            'nodos_con_mediciones': sum(
                1 for nodo in self.arbol.nodos.values()
                if nodo.numero_mediciones > 0
            ),
            'nodos_hoja': sum(
                1 for nodo in self.arbol.nodos.values()
                if nodo.es_hoja()
            ),
            'total_mediciones': sum(
                nodo.numero_mediciones for nodo
                in self.arbol.nodos.values()
            )
        }

        return stats

    def _crear_nodos(
        self,
        conceptos: List[Concepto]
    ):
        """Crea un nodo para cada concepto"""
        for concepto in conceptos:
            nodo = NodoConcepto(
                concepto=concepto,
                archivo_origen=concepto.archivo_origen
            )
            self.arbol.agregar_nodo(nodo)

        logger.info(f"Creados {len(conceptos)} nodos")

    def _procesar_descomposiciones(
        self,
        descomposiciones: List[Descomposicion]
    ):
        """Establece las relaciones padre-hijo desde las descomposiciones"""
        relaciones = 0

        for desc in descomposiciones:
            codigo_padre = desc.codigo_padre

            # Verificar que el padre existe
            if codigo_padre not in self.arbol.nodos:
                logger.warning(
                    f"Padre {codigo_padre} no encontrado en conceptos")
                continue

            for componente in desc.componentes:
                codigo_hijo = componente.codigo_componente

                # Verificar que el hijo existe
                if codigo_hijo not in self.arbol.nodos:
                    logger.warning(
                        f"Hijo {codigo_hijo} no encontrado en conceptos")
                    continue

                # Establecer relación
                self.relaciones_padre_hijo[codigo_padre].add(codigo_hijo)
                relaciones += 1

                logger.debug(f"Relación: {codigo_padre} -> {codigo_hijo}")

        logger.info(f"Procesadas {len(descomposiciones)} descomposiciones, "
                    f"encontradas {relaciones} relaciones válidas")

        # Debug: Mostrar algunas relaciones para verificar
        if logger.isEnabledFor(logging.DEBUG):
            for padre, hijos in list(self.relaciones_padre_hijo.items())[:5]:
                logger.debug(f"  {padre} tiene hijos: {list(hijos)}")

    def _detectar_jerarquia_por_codigo(self, conceptos: List[Concepto]):
        """
        Detecta jerarquía por estructura de códigos
        (ej: Cap1, Cap1.1, Cap1.1.1)
        """
        # Agrupar conceptos por tipo para identificar jerarquías
        capitulos_por_nivel = defaultdict(list)

        for concepto in conceptos:
            if concepto.es_capitulo or concepto.tipo in ['0', '1']:
                # Detectar nivel por la estructura del código
                nivel = self._detectar_nivel_por_codigo(concepto.codigo)
                capitulos_por_nivel[nivel].append(concepto)

        relaciones_jerarquicas = 0

        # Establecer relaciones jerárquicas
        for nivel in sorted(capitulos_por_nivel.keys()):
            if nivel == 0:
                continue  # Los de nivel 0 son raíces

            for concepto in capitulos_por_nivel[nivel]:
                padre_codigo = self._encontrar_padre_por_codigo(
                    concepto.codigo,
                    capitulos_por_nivel[nivel - 1] if nivel > 0 else []
                )

                if padre_codigo:
                    self.relaciones_padre_hijo[padre_codigo].add(
                        concepto.codigo)
                    relaciones_jerarquicas += 1
                    logger.debug(
                        f"Jerarquía por código: {padre_codigo} ->"
                        f"{concepto.codigo}"
                    )

        logger.info("Detectada jerarquía por código: " +
                    f"{relaciones_jerarquicas} relaciones en"
                    f"{len(capitulos_por_nivel)} niveles"
                    )

    def _detectar_nivel_por_codigo(
        self,
        codigo: str
    ) -> int:
        """Detecta el nivel jerárquico por la estructura del código"""
        # Contar puntos para códigos tipo "Cap1.1.1"
        if '.' in codigo:
            return codigo.count('.')

        # Contar # para códigos tipo "###"
        if '#' in codigo:
            return codigo.count('#')

        # Detectar por prefijos comunes
        if any(prefix in codigo.lower() for prefix in [
                'cap', 'subcap', 'apartado']):
            # Análisis más sofisticado si es necesario
            return 0

        return 0

    def _encontrar_padre_por_codigo(
        self,
        codigo_hijo: str,
        conceptos_nivel_superior: List[Concepto]
    ) -> str:
        """Encuentra el padre más probable por estructura de código"""
        if not conceptos_nivel_superior:
            return None

        # Para códigos con puntos (ej: 1.1.1 → padre es 1.1)
        if '.' in codigo_hijo:
            partes = codigo_hijo.split('.')
            if len(partes) > 1:
                codigo_padre_esperado = '.'.join(partes[:-1])

                # Buscar concepto con este código
                for concepto in conceptos_nivel_superior:
                    if concepto.codigo == codigo_padre_esperado:
                        return concepto.codigo

                # Buscar por prefijo más similar
                for concepto in conceptos_nivel_superior:
                    if codigo_hijo.startswith(concepto.codigo + '.'):
                        return concepto.codigo

        return None

    def _asociar_mediciones(
        self,
        mediciones: List[Medicion]
    ):
        """
        Asocia mediciones a sus conceptos correspondientes
        con validación de contexto padre-hijo

        REGLAS DE ASOCIACIÓN:
        1. Si medicion.codigo_padre existe:
            asociar solo si el concepto tiene ese padre
        2. Si medicion.codigo_padre es None:
            asociar directamente al codigo_hijo
        3. Registro detallado de asociaciones y rechazos
        """
        stats = {
            'mediciones_asociadas': 0,
            'mediciones_rechazadas_padre': 0,
            'mediciones_sin_concepto': 0,
            'mediciones_sin_padre_definido': 0
        }

        logger.info(
            "Iniciando asociación de mediciones con validación padre-hijo...")

        for medicion in mediciones:
            codigo_concepto = medicion.codigo_hijo
            codigo_padre_medicion = medicion.codigo_padre

            # Verificar que el concepto hijo existe
            if codigo_concepto not in self.arbol.nodos:
                logger.debug(
                    f"Concepto {codigo_concepto} no encontrado" +
                    "- medición rechazada")
                stats['mediciones_sin_concepto'] += 1
                continue

            nodo_concepto = self.arbol.nodos[codigo_concepto]

            # CASO 1: Medición con código padre específico
            if codigo_padre_medicion is not None:
                # Verificar que el padre del concepto coincide
                # con el padre de la medición
                if nodo_concepto.codigo_padre == codigo_padre_medicion:
                    # ASOCIACIÓN VÁLIDA: padre coincide
                    self.arbol.agregar_medicion_a_concepto(
                        codigo_concepto, medicion)
                    stats['mediciones_asociadas'] += 1

                    logger.debug(
                        f" Medición asociada: {codigo_concepto} "
                        f"(padre: {codigo_padre_medicion})"
                    )
                else:
                    #  RECHAZO: padre no coincide
                    stats['mediciones_rechazadas_padre'] += 1

                    logger.debug(
                        f" Medición rechazada: {codigo_concepto} "
                        f"(padre medición: {codigo_padre_medicion}, "
                        f"padre concepto: {nodo_concepto.codigo_padre})"
                    )

            # CASO 2: Medición sin código padre (mediciones no estructuradas)
            else:
                #  ASOCIACIÓN DIRECTA: sin restricción de padre
                self.arbol.agregar_medicion_a_concepto(
                    codigo_concepto, medicion)
                stats['mediciones_asociadas'] += 1
                stats['mediciones_sin_padre_definido'] += 1

                logger.debug(
                    f" Medición directa asociada: {codigo_concepto} "
                    f"(sin padre definido)"
                )

        # Logging de resultados
        logger.info("=== RESULTADOS ASOCIACIÓN DE MEDICIONES ===")
        logger.info(f" Mediciones asociadas: {stats['mediciones_asociadas']}")
        logger.info(
            f" Rechazadas por padre: {stats['mediciones_rechazadas_padre']}")
        logger.info(
            f" Concepto no encontrado: {stats['mediciones_sin_concepto']}")
        logger.info(
            f"  Sin padre definido: {stats['mediciones_sin_padre_definido']}")

        # Verificación adicional: mostrar algunos ejemplos
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("=== EJEMPLOS DE ASOCIACIONES ===")
            nodos_con_mediciones = 0

            for codigo, nodo in self.arbol.nodos.items():
                if nodo.numero_mediciones > 0:
                    nodos_con_mediciones += 1
                    if nodos_con_mediciones <= 5:
                        logger.debug(
                            f"Nodo {codigo} (padre: {nodo.codigo_padre}): "
                            f"{nodo.numero_mediciones} mediciones"
                        )

        return stats

    def _construir_estructura_final(self):
        """Construye la estructura final del árbol"""
        logger.info("Construyendo estructura final del árbol...")

        # Debug: Mostrar cuántas relaciones tenemos
        total_relaciones = sum(len(hijos) for hijos
                               in self.relaciones_padre_hijo.values())
        logger.info(
            f"Total de relaciones padre-hijo a procesar: {total_relaciones}")

        # 1. Identificar nodos raíz ANTES de establecer relaciones
        self._identificar_raices_preliminar()

        # 2. Establecer relaciones básicas padre-hijo (sin niveles aún)
        relaciones_establecidas = 0
        for codigo_padre, codigos_hijos in self.relaciones_padre_hijo.items():
            logger.debug(
                f"Procesando padre {codigo_padre} con"
                f"{len(codigos_hijos)} hijos"
            )

            for codigo_hijo in codigos_hijos:
                # Verificar que ambos nodos existen antes de
                # establecer la relación
                if (
                    codigo_padre in self.arbol.nodos and
                    codigo_hijo in self.arbol.nodos
                ):
                    # Establecer relación básica SIN calcular niveles aún
                    exito = self._establecer_relacion_basica(
                        codigo_padre, codigo_hijo)
                    if exito:
                        relaciones_establecidas += 1
                        logger.debug(
                            f"  Relación establecida: {codigo_padre}"
                            f" -> {codigo_hijo}"
                        )
                    else:
                        logger.warning(
                            f"  Relación rechazada (circular): {codigo_padre}"
                            f" -> {codigo_hijo}"
                        )
                else:
                    logger.warning(
                        f"  No se pudo establecer relación {codigo_padre} ->"
                        f" {codigo_hijo}: nodos no encontrados"
                    )

        logger.info(
            f"Relaciones padre-hijo establecidas: {relaciones_establecidas}")

        # 3. Calcular niveles jerárquicos sistemáticamente
        self._calcular_niveles_jerarquicos()

        # 4. Actualizar índices por nivel
        self._actualizar_indices_por_nivel()

        # 5. Calcular propiedades de todos los nodos
        for codigo, nodo in self.arbol.nodos.items():
            nodo.calcular_propiedades()

        # Debug: Mostrar algunos nodos con hijos para verificar
        nodos_con_hijos = 0
        for codigo, nodo in self.arbol.nodos.items():
            if nodo.tiene_hijos:
                nodos_con_hijos += 1
                if nodos_con_hijos <= 5:  # Mostrar solo los primeros 5
                    logger.debug(
                        f"Nodo {codigo} (nivel {nodo.nivel_jerarquico}) "
                        f"tiene {nodo.numero_hijos} hijos: "
                        f"{nodo.codigos_hijos}"
                    )

        logger.info(f"Estructura final: {len(self.arbol.nodos_raiz)} "
                    f"raíces identificadas, {nodos_con_hijos} nodos con hijos"
                    )

    def _identificar_raices_preliminar(self):
        """Identifica los nodos raíz antes de establecer relaciones"""
        # Limpiar lista de raíces existente
        self.arbol.nodos_raiz.clear()

        # Todos los hijos conocidos
        todos_los_hijos = set()
        for hijos in self.relaciones_padre_hijo.values():
            todos_los_hijos.update(hijos)

        logger.debug(
            f"Total de nodos que son hijos de alguien: {len(todos_los_hijos)}")

        # Los nodos que no son hijos de nadie son raíces
        for codigo, nodo in self.arbol.nodos.items():
            if codigo not in todos_los_hijos:
                self.arbol.nodos_raiz.append(codigo)
                # Establecer propiedades básicas de raíz
                nodo.codigo_padre = None
                nodo.nivel_jerarquico = 0
                nodo.ruta_completa = []

        logger.info(f"Identificadas {len(self.arbol.nodos_raiz)} raíces")

        # Debug: Mostrar algunas raíces
        if logger.isEnabledFor(logging.DEBUG) and self.arbol.nodos_raiz:
            for i, raiz in enumerate(self.arbol.nodos_raiz[:5]):
                nodo_raiz = self.arbol.nodos[raiz]
                logger.debug(
                    f"  Raíz {i+1}: {raiz} - "
                    f"{(nodo_raiz.concepto.resumen[:50]
                        if nodo_raiz.concepto.resumen else 'Sin resumen')}")

    def _establecer_relacion_basica(
        self,
        codigo_padre: str,
        codigo_hijo: str
    ) -> bool:
        """Establece una relación padre-hijo básica sin calcular niveles"""
        if (
            codigo_padre in self.arbol.nodos
            and codigo_hijo in self.arbol.nodos
        ):
            # Evitar relaciones circulares
            if codigo_hijo == codigo_padre:
                return False

            # Evitar que un nodo sea padre de su propio ancestro
            hijo = self.arbol.nodos[codigo_hijo]
            if hijo.codigo_padre and self._es_ancestro(
                    codigo_hijo, codigo_padre):
                return False

            # Establecer relación básica
            self.arbol.nodos[codigo_padre].agregar_hijo(codigo_hijo)
            hijo.codigo_padre = codigo_padre

            # NO calcular niveles aquí - se hace después sistemáticamente
            return True
        return False

    def _calcular_niveles_jerarquicos(self):
        """Calcula los niveles jerárquicos de forma sistemática usando BFS"""
        logger.info("Calculando niveles jerárquicos...")

        # Usar BFS (Breadth-First Search) para calcular niveles
        # Esto garantiza que los niveles se calculen en orden correcto

        queue = deque()
        visitados = set()

        # Inicializar con las raíces (nivel 0)
        for codigo_raiz in self.arbol.nodos_raiz:
            if codigo_raiz in self.arbol.nodos:
                nodo_raiz = self.arbol.nodos[codigo_raiz]
                nodo_raiz.nivel_jerarquico = 0
                nodo_raiz.ruta_completa = []
                queue.append((codigo_raiz, 0))
                visitados.add(codigo_raiz)
                logger.debug(f"Raíz inicializada: {codigo_raiz} nivel 0")

        # BFS para propagar niveles
        while queue:
            codigo_actual, nivel_actual = queue.popleft()
            nodo_actual = self.arbol.nodos[codigo_actual]

            # Procesar todos los hijos del nodo actual
            for codigo_hijo in nodo_actual.codigos_hijos:
                if (
                    codigo_hijo in self.arbol.nodos and
                    codigo_hijo not in visitados
                ):
                    nodo_hijo = self.arbol.nodos[codigo_hijo]

                    # Calcular nivel y ruta del hijo
                    nivel_hijo = nivel_actual + 1
                    ruta_hijo = nodo_actual.ruta_completa + [codigo_actual]

                    # Asignar propiedades
                    nodo_hijo.nivel_jerarquico = nivel_hijo
                    nodo_hijo.ruta_completa = ruta_hijo

                    # Agregar a la cola para procesar sus hijos
                    queue.append((codigo_hijo, nivel_hijo))
                    visitados.add(codigo_hijo)

                    logger.debug(
                        f"Nivel calculado: {codigo_hijo} nivel {nivel_hijo} "
                        f"(padre: {codigo_actual})"
                    )

        logger.info(f"Niveles calculados para {len(visitados)} nodos")

        # Verificar si hay nodos sin procesar (huérfanos o ciclos)
        nodos_sin_procesar = set(self.arbol.nodos.keys()) - visitados
        if nodos_sin_procesar:
            logger.warning(
                f"Nodos no procesados (posibles huérfanos): "
                f"{list(nodos_sin_procesar)[:10]}")

            # Asignar nivel 0 a nodos huérfanos
            for codigo in nodos_sin_procesar:
                nodo = self.arbol.nodos[codigo]
                nodo.nivel_jerarquico = 0
                nodo.ruta_completa = []
                # Añadir como raíz si no tiene padre
                if nodo.codigo_padre is None:
                    self.arbol.nodos_raiz.append(codigo)

    def _actualizar_indices_por_nivel(self):
        """Actualiza los índices de nodos por nivel"""
        logger.info("Actualizando índices por nivel...")

        # Limpiar índices existentes
        self.arbol.nodos_por_nivel.clear()

        # Reconstruir índices basados en niveles calculados
        for codigo, nodo in self.arbol.nodos.items():
            nivel = nodo.nivel_jerarquico

            if nivel not in self.arbol.nodos_por_nivel:
                self.arbol.nodos_por_nivel[nivel] = []

            if codigo not in self.arbol.nodos_por_nivel[nivel]:
                self.arbol.nodos_por_nivel[nivel].append(codigo)

        # Calcular estadísticas finales
        self.arbol.calcular_estadisticas()

        # Debug: Mostrar distribución por niveles
        if logger.isEnabledFor(logging.DEBUG):
            for nivel in sorted(self.arbol.nodos_por_nivel.keys()):
                cantidad = len(self.arbol.nodos_por_nivel[nivel])
                logger.debug(f"  Nivel {nivel}: {cantidad} nodos")

    def _es_ancestro(self, posible_ancestro: str, nodo: str) -> bool:
        """Verifica si un nodo es ancestro de otro (para evitar ciclos)"""
        actual = nodo
        while actual in self.arbol.nodos:
            nodo_actual = self.arbol.nodos[actual]
            if nodo_actual.codigo_padre == posible_ancestro:
                return True
            actual = nodo_actual.codigo_padre
            if not actual:
                break
        return False
