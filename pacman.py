
# math: raices y potencias
# random: elegir algo al azar
# sys: cerrar el programa
# pygame: la ventana, el dibujo y el teclado
import math
import random
import sys
from collections import deque

import pygame


# Estos numeros no se piensan cambiar, por eso van en mayuscula
# Cada casilla del mapa mide 28 pixeles
# El mapa tiene 28 columnas y 21 filas
TILE_SIZE = 28
MAP_WIDTH = 28
MAP_HEIGHT = 21

# La ventana es el mapa, mas 70 pixeles abajo para el puntaje
SCREEN_WIDTH = MAP_WIDTH * TILE_SIZE
SCREEN_HEIGHT = MAP_HEIGHT * TILE_SIZE + 70
# El juego intenta dibujar 60 veces por segundo
FPS = 60

# Son rojo, verde y azul, de 0 a 255
# (255, 230, 0) es el amarillo de Pac-Man
COLOR_FONDO = (5, 5, 25)
COLOR_MURO = (25, 45, 180)
COLOR_MURO_BORDE = (80, 110, 255)
COLOR_JUGADOR = (255, 230, 0)
COLOR_PUNTO = (255, 220, 150)
COLOR_TEXTO = (255, 255, 255)
COLOR_ROJO = (255, 60, 60)



# En Python se empieza a contar desde 0
# ** 2 significa al cuadrado
# Esta funcion mide que tan lejos estan dos puntos
def distancia(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


# Pasa una casilla (columna, fila) al pixel del medio de esa casilla
# // es division entera: 28 // 2 da 14, sin decimales
# Devuelve los dos numeros juntos, en una tupla
def centro_de_celda(columna, fila):
    return (
        columna * TILE_SIZE + TILE_SIZE // 2,
        fila * TILE_SIZE + TILE_SIZE // 2,
    )


# Pasa de pixeles al numero de casilla
# Error de antes: en el historial se usaba round(x / 28)
# El centro de una casilla cae en 14, 42, 70... y round(42 / 28) = round(1.5) = 2,
# o sea la casilla de al lado El verde seguia un rastro corrido
# Cambio: se resta el medio de la casilla y despues se redondea
def celda_desde_pixel(x, y):
    return (
        int(round((x - TILE_SIZE / 2) / TILE_SIZE)),
        int(round((y - TILE_SIZE / 2) / TILE_SIZE)),
    )


# Error de antes: si el destino caia dentro de un muro o afuera del mapa,
# el fantasma igual caminaba hacia ese punto y se perdia contra la pared
# Cambio: se busca la casilla libre mas cercana y el camino llega ahi
# min elige la casilla con el numero mas chico
# key=lambda le dice que numero usar para comparar
# abs saca el signo: de 3 a 1 hay 2, igual que de 1 a 3
def celda_libre_mas_cercana(celda, celdas_libres):
    if celda in celdas_libres:
        return celda
    return min(
        celdas_libres,
        key=lambda libre: abs(libre[0] - celda[0]) + abs(libre[1] - celda[1]),
    )


# Error de antes: cada fantasma elegia el vecino que se veia mas cerca en linea recta
# No miraba si mas adelante el pasillo estaba cerrado, entraba a un callejon,
# daba la vuelta, y parecia que iban al azar
# Cambio: se arma cuantos pasos faltan hasta el destino, solo por casillas libres
# deque es una fila El primero que entra es el primero que sale
# Entonses el recorrido sale en orden, casilla por casilla
def distancias_hasta(destino, celdas_libres):
    distancias = {destino: 0}
    pendientes = deque([destino])
    # while repite mientras la condicion sea verdadera
    # Aca, mientras queden casillas en la fila
    while pendientes:
        columna, fila = pendientes.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            vecino = (columna + dx, fila + dy)
            if vecino in celdas_libres and vecino not in distancias:
                distancias[vecino] = distancias[(columna, fila)] + 1
                pendientes.append(vecino)
    return distancias


# class es un molde Punto describe como es un puntito
# Todavia no existe ningun punto: se crean mas adelante
# self significa "este punto", el que se esta usando en ese momento
class Punto:
    # __init__ corre solo cuando se crea un punto nuevo
    # Guarda la casilla, el centro en pixeles, el radio
    # y que todavia no se lo comieron
    def __init__(self, columna, fila):
        self.columna = columna
        self.fila = fila
        self.x, self.y = centro_de_celda(columna, fila)
        self.radio = 4
        self.activo = True

    # if pregunta Si la condicion es verdadera, corre lo que esta indentado debajo
    # Aca: si el punto sigue activo, se dibuja Si ya fue comido, no se hace nada
    # y desaparece de la pantalla
    def dibujar(self, pantalla):
        if self.activo:
            pygame.draw.circle(pantalla, COLOR_PUNTO, (self.x, self.y), self.radio)


# Molde de Pac-Man
class Jugador:
    # Se ubica en el centro de su casilla
    # Velocidad 3 = se mueve 3 pixeles por fotograma
    # Una direccion es una tupla de dos numeros:
    # (1, 0) derecha, (-1, 0) izquierda, (0, -1) arriba, (0, 1) abajo
    # En la pantalla la y crece hacia abajo, por eso arriba es negativo
    # (0, 0) significa quieto
    # direccion es hacia donde va ahora
    # direccion_solicitada es la flecha que se apreto, aunque todavia no pueda doblar
    # rect es un rectangulo invisible del tamaño del cuerpo
    # Sirve para chocar con muros y fantasmas En pantalla se ve un circulo
    def __init__(self, columna, fila):
        self.x, self.y = centro_de_celda(columna, fila)
        self.radio = TILE_SIZE // 2 - 3
        self.velocidad = 3
        self.direccion = (0, 0)
        self.direccion_solicitada = (0, 0)
        # El rosa y el cian miran hacia donde mira Pac-Man
        # Error de antes: quieto, la direccion era (0, 0) y esos dos
        # apuntaban al mismo lugar que el rojo
        # Cambio: si esta quieto, usan la ultima flecha
        # Al empezar, esa flecha es la isquierda
        self.ultima_direccion = (-1, 0)
        self.rect = pygame.Rect(0, 0, self.radio * 2, self.radio * 2)
        self.actualizar_rectangulo()

    # Mueve el rectangulo invisible al centro de Pac-Man
    # round redondea, porque el rectangulo necesita numeros enteros
    def actualizar_rectangulo(self):
        self.rect.center = (round(self.x), round(self.y))

    # Esto no mueve a Pac-Man Solo anota la direccion que pidio el teclado
    # El movimiento de verdad pasa en actualizar, si el camino esta libre
    def establecer_direccion(self, direccion):
        self.direccion_solicitada = direccion

    # Revisa si se puede mover dx pixeles en x y dy en y
    # Copia el rectangulo, lo adelanta y mira si toca algun muro
    # any recorre los muros y da True si alguno choca
    # not le da vuelta al resultado: True significa que el camino esta libre
    # El for de adentro significa "por cada muro de la lista"
    def puede_moverse(self, dx, dy, muros):
        prueba = self.rect.copy()
        prueba.center = (round(self.x + dx), round(self.y + dy))
        return not any(prueba.colliderect(muro) for muro in muros)

    # Corre una vez por fotograma
    # Primero: si la flecha pedida no choca, esa pasa a ser la direccion real
    # Asi se puede apretar la flecha un poco antes de la esquina y dobla cuando puede
    # Despues avanza Si ahi si choca, se detiene y la direccion queda en (0, 0)
    # += suma y guarda el resultado en la misma variable
    def actualizar(self, muros):
        dx_solicitada, dy_solicitada = self.direccion_solicitada
        if self.puede_moverse(
            dx_solicitada * self.velocidad,
            dy_solicitada * self.velocidad,
            muros,
        ):
            self.direccion = self.direccion_solicitada

        if self.direccion != (0, 0):
            self.ultima_direccion = self.direccion

        dx, dy = self.direccion
        movimiento_x = dx * self.velocidad
        movimiento_y = dy * self.velocidad

        if self.puede_moverse(movimiento_x, movimiento_y, muros):
            self.x += movimiento_x
            self.y += movimiento_y
        else:
            self.direccion = (0, 0)

        self.actualizar_rectangulo()

    # Dibuja el circulo amarillo
    # Si esta quieto, return sale de la funcion y no dibuja la boca
    # Si se mueve, arma un triangulo del lado hacia donde mira
    # y lo pinta del color del fondo Ese triangulo es el hueco de la boca
    # elif es "si lo de arriba no paso, fijarse esta otra cosa"
    # else es "si ninguna de las anteriores paso"
    def dibujar(self, pantalla):
        pygame.draw.circle(
            pantalla,
            COLOR_JUGADOR,
            (round(self.x), round(self.y)),
            self.radio,
        )

        dx, dy = self.direccion
        if dx == 0 and dy == 0:
            return

        if dx > 0:
            puntos_boca = [
                (self.x, self.y),
                (self.x + self.radio, self.y - self.radio // 2),
                (self.x + self.radio, self.y + self.radio // 2),
            ]
        elif dx < 0:
            puntos_boca = [
                (self.x, self.y),
                (self.x - self.radio, self.y - self.radio // 2),
                (self.x - self.radio, self.y + self.radio // 2),
            ]
        elif dy < 0:
            puntos_boca = [
                (self.x, self.y),
                (self.x - self.radio // 2, self.y - self.radio),
                (self.x + self.radio // 2, self.y - self.radio),
            ]
        else:
            puntos_boca = [
                (self.x, self.y),
                (self.x - self.radio // 2, self.y + self.radio),
                (self.x + self.radio // 2, self.y + self.radio),
            ]

        pygame.draw.polygon(pantalla, COLOR_FONDO, puntos_boca)


# Molde de un fantasma Cada uno tiene un numero del 1 al 6
# y ese numero cambia a donde quiere llegar
# El camino lo buscan todos igual: por las casillas libres, de centro a centro
class Fantasma:
    # Estas listas son de la clase Las comparten todos los fantasmas
    # [] es una lista: se puede recorrer y tiene un orden
    COLORES = [
        (255, 50, 50),
        (255, 140, 255),
        (0, 230, 255),
        (255, 150, 0),
        (100, 255, 100),
        (180, 100, 255),
    ]
    DIRECCIONES = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    # % es el resto de una division Sirve para no salirse de la lista de colores
    # Error de antes: la velocidad era 1.8 y cada fantasma sumaba 0.08
    # 28 no es multiplo de 1.8, entonses nunca caian justo en el centro
    # y se iban chocando de costado
    # Cambio: todos van a 2 pixeles 28 / 2 = 14, asi que de un centro
    # al siguiente caen exacto
    # La direccion arranca en (0, 0) Antes arrancaba al azar y,
    # como podian dar media vuelta enseguida, salian temblando
    def __init__(self, columna, fila, numero):
        self.x, self.y = centro_de_celda(columna, fila)
        self.numero = numero
        self.color = self.COLORES[(numero - 1) % len(self.COLORES)]
        self.radio = TILE_SIZE // 2 - 3
        self.velocidad = 2
        self.direccion = (0, 0)
        # El rojo, que es el primero, espera 2 segundos antes de salir
        # El juego da 60 vueltas por segundo, entonces 2 * 60 = 120 fotogramas quieto
        # Error de antes: salia en el primer fotograma y no daba tiempo a moverse
        # Los otros nacen despues, cuando sube el puntaje, y esos no esperan
        # Al apretar R tambien espera, porque reiniciar crea este fantasma de nuevo
        self.espera = 2 * FPS if numero == 1 else 0
        self.rect = pygame.Rect(0, 0, self.radio * 2, self.radio * 2)
        self.actualizar_rectangulo()

    # Mueve el rectangulo invisible al centro del fantasma
    def actualizar_rectangulo(self):
        self.rect.center = (round(self.x), round(self.y))

    # Devuelve la columna y la fila donde esta parado
    def celda_actual(self):
        return celda_desde_pixel(self.x, self.y)

    # Error de antes: "cerca del centro" usaba round(x / 28) * 28
    # Eso cae en 0, 28, 56: el borde entre dos casillas, no el medio (14, 42, 70)
    # Giraban encima de la linea El cuerpo de 22 pixeles pisaba el muro
    # del hueco chico, y el rojo se quedaba rebotando arriba y abajo
    # Cambio: solo es True cuando x e y estan justo en el medio
    # % es el resto Si da 0, cayo en el centro
    def en_el_centro(self):
        return (
            (self.x - TILE_SIZE // 2) % TILE_SIZE == 0
            and (self.y - TILE_SIZE // 2) % TILE_SIZE == 0
        )

    # Error de antes: miraba 5 pixeles para adelante con el rectangulo (velocidad * 3)
    # Un hueco parecia abierto y, al moverse, el cuerpo igual chocaba
    # Cambio: se pregunta si la casilla de al lado esta en el conjunto de pasillos
    def puede_entrar(self, columna, fila, direccion, celdas_libres):
        dx, dy = direccion
        return (columna + dx, fila + dy) in celdas_libres

    # Error de antes: las 4 flechas servian, incluida la de atras
    # En un pasillo el rojo elegia arriba, al toque abajo, y no avanzaba
    # Cambio: se saca la media vuelta Solo se deja si es la unica salida
    # Si todavia no camino, direccion es (0, 0) y la opuesta tambien,
    # asi que la primera eleccion puede ser cualquiera de las cuatro
    # El menos cambia el signo: (1, 0) pasa a ser (-1, 0)
    # La lista de abajo es un for y un if en una sola linea
    # Se queda con cada flecha que no sea la de atras y que entre al pasillo
    def direcciones_sin_vuelta(self, columna, fila, celdas_libres):
        opuesta = (-self.direccion[0], -self.direccion[1])
        validas = [
            direccion
            for direccion in self.DIRECCIONES
            if direccion != opuesta
            and self.puede_entrar(columna, fila, direccion, celdas_libres)
        ]
        if validas:
            return validas
        if self.puede_entrar(columna, fila, opuesta, celdas_libres):
            return [opuesta]
        return []

    # Si Pac-Man se esta moviendo, se usa esa flecha
    # Si esta quieto, se usa la ultima Antes la flecha quieta era (0, 0)
    # y el rosa y el cian se quedaban sin adelanto
    def mira_del_jugador(self, jugador):
        if jugador.direccion != (0, 0):
            return jugador.direccion
        return jugador.ultima_direccion

    # La casilla a la que el fantasma quiere llegar
    # El camino hasta ahi lo arma distancias_hasta
    # None significa que este fantasma no usa un destino (el violeta)
    def celda_destino(self, jugador, fantasmas, historial_jugador):
        celda_jugador = celda_desde_pixel(jugador.x, jugador.y)

        # Rojo Error de antes: apuntaba al pixel de Pac-Man y daba un paso
        # hacia lo que se viera mas cerca, sin rodear muros
        # Cambio: la casilla de Pac-Man es el destino y va por el pasillo
        if self.numero == 1:
            return celda_jugador

        # Rosa Tiene que aparecer 4 casillas adelante de Pac-Man
        # para cortarle el camino
        # Error de antes: si Pac-Man estaba quieto, dx y dy valian 0
        # y este punto era el mismo que el del rojo
        # Cambio: se usa la ultima flecha que miro
        if self.numero == 2:
            dx, dy = self.mira_del_jugador(jugador)
            return (celda_jugador[0] + dx * 4, celda_jugador[1] + dy * 4)

        # Cian Calcula 2 casillas adelante de Pac-Man y las espeja
        # contra el rojo, para salir por el otro lado y encerrarlo
        # Error de antes: ese punto se armaba en pixeles y muchas veces caia
        # dentro de un muro El cian caminaba derecho ahi y daba vueltas
        # Si el punto no es pasillo, celda_libre_mas_cercana lo corrige
        if self.numero == 3:
            dx, dy = self.mira_del_jugador(jugador)
            adelante = (
                celda_jugador[0] + dx * 2,
                celda_jugador[1] + dy * 2,
            )
            rojo = celda_desde_pixel(fantasmas[0].x, fantasmas[0].y)
            return (
                adelante[0] + (adelante[0] - rojo[0]),
                adelante[1] + (adelante[1] - rojo[1]),
            )

        # Naranja, cuando esta lejos Cuando esta cerca, huye en elegir_direccion,
        # no aca Error de antes: lejos tambien iba en linea recta
        # Cambio: persigue la casilla de Pac-Man por el pasillo, igual que el rojo
        if self.numero == 4:
            return celda_jugador

        # Verde Error de antes: iba al punto mas viejo del historial en linea recta,
        # y ese punto ademas estaba en la casilla equivocada
        # Cambio: el historial es una lista de casillas, de la mas vieja a la mas nueva,
        # y el verde camina a la que sigue en esa lista
        if self.numero == 5:
            return self.siguiente_del_rastro(historial_jugador)

        return None

    # Si el fantasma esta parado en el rastro, el destino es la casilla siguiente
    # Si no, primero va a la mas vieja para engancharse al camino de Pac-Man
    # enumerate da el indice y la casilla Se queda con la ultima vez
    # que esa casilla aparece, para seguir hacia adelante y no hacia atras
    def siguiente_del_rastro(self, historial):
        if not historial:
            return None
        actual = self.celda_actual()
        indice = None
        for i, celda in enumerate(historial):
            if celda == actual:
                indice = i
        if indice is None:
            return historial[0]
        if indice + 1 < len(historial):
            return historial[indice + 1]
        return historial[indice]

    # Da True si Pac-Man esta a menos de 8 casillas Lo usa el naranja para huir
    def jugador_esta_cerca(self, jugador):
        return distancia((self.x, self.y), (jugador.x, jugador.y)) < TILE_SIZE * 8

    # Elige una flecha, una sola vez, parado en el centro de la casilla
    def elegir_direccion(self, celdas_libres, jugador, fantasmas, historial_jugador):
        columna, fila = self.celda_actual()
        validas = self.direcciones_sin_vuelta(columna, fila, celdas_libres)
        if not validas:
            return

        # Violeta Error de antes: sorteaba una flecha en cada casilla,
        # aunque el pasillo siguiera derecho, y se veia como ruido
        # Cambio: si puede seguir derecho, sigue Sortea solo cuando
        # el pasillo se corta y tiene que doblar una esquina
        # random.choice agarra una de la lista, al azar
        # La media vuelta solo entra en validas si no hay otra salida
        if self.numero == 6:
            if self.direccion in validas:
                return
            self.direccion = random.choice(validas)
            return

        # Naranja cerca de Pac-Man Error de antes: huia a la esquina mas lejana
        # en linea recta, y el pasillo hacia esa esquina a veces
        # pasaba por Pac-Man O sea que, huyendo, se le acercaba
        # Cambio: de las salidas que hay, elige la que lo deja mas lejos
        # Como no puede dar media vuelta, no se queda subiendo y bajando
        if self.numero == 4 and self.jugador_esta_cerca(jugador):
            celda_jugador = celda_desde_pixel(jugador.x, jugador.y)
            mejor = validas[0]
            mejor_lejos = -1
            for direccion in validas:
                dx, dy = direccion
                vecino = (columna + dx, fila + dy)
                lejos = abs(vecino[0] - celda_jugador[0]) + abs(vecino[1] - celda_jugador[1])
                if lejos > mejor_lejos:
                    mejor_lejos = lejos
                    mejor = direccion
            self.direccion = mejor
            return

        destino = self.celda_destino(jugador, fantasmas, historial_jugador)
        if destino is None:
            if self.direccion in validas:
                return
            self.direccion = random.choice(validas)
            return

        destino = celda_libre_mas_cercana(destino, celdas_libres)
        # Si ya esta en el destino, sigue por la flecha que traia
        # para no quedarse trabado girando en la misma casilla
        if (columna, fila) == destino:
            if self.direccion in validas:
                return
            self.direccion = validas[0]
            return

        # De las salidas sin media vuelta, se queda con la que menos pasos tiene
        # Eso es el primer paso del camino real, no el vecino que se ve mas cerca
        distancias = distancias_hasta(destino, celdas_libres)
        mejor = None
        mejor_distancia = None
        for direccion in validas:
            dx, dy = direccion
            vecino = (columna + dx, fila + dy)
            if vecino not in distancias:
                continue
            if mejor_distancia is None or distancias[vecino] < mejor_distancia:
                mejor_distancia = distancias[vecino]
                mejor = direccion
        if mejor is None:
            self.direccion = validas[0]
            return
        self.direccion = mejor

    # Un fotograma del fantasma
    # Error de antes: elegia flecha varias veces mientras pasaba por el borde,
    # y si el paso chocaba la elegia otra vez al instante Por eso rebotaban
    # Cambio: elige solo al caer en el centro, y esa flecha se mantiene
    # hasta el centro de la casilla que sigue
    def actualizar(self, celdas_libres, jugador, fantasmas, historial_jugador):
        # Mientras espera, no elige camino ni se mueve
        # Resta 1 por vuelta Cuando llega a 0, ahi recien empieza a perseguir
        if self.espera > 0:
            self.espera -= 1
            return

        if self.en_el_centro():
            self.x, self.y = centro_de_celda(*self.celda_actual())
            self.elegir_direccion(
                celdas_libres, jugador, fantasmas, historial_jugador
            )
            columna, fila = self.celda_actual()
            if not self.puede_entrar(columna, fila, self.direccion, celdas_libres):
                self.actualizar_rectangulo()
                return

        dx, dy = self.direccion
        self.x += dx * self.velocidad
        self.y += dy * self.velocidad
        self.actualizar_rectangulo()

    # Arma el fantasma con varias formas:
    # un circulo (cabeza), un rectangulo (cuerpo),
    # circulos chicos abajo (la onda de la savana) y dos ojos
    # range(inicio, fin, paso) da numeros desde inicio hasta antes de fin, saltando de a "paso"
    # for desplazamiento in (-6, 6) repite dos veces: una para cada ojo
    def dibujar(self, pantalla):
        x = round(self.x)
        y = round(self.y)

        pygame.draw.circle(pantalla, self.color, (x, y - 3), self.radio)
        base_rect = pygame.Rect(
            x - self.radio,
            y - 3,
            self.radio * 2,
            self.radio + 7,
        )
        pygame.draw.rect(pantalla, self.color, base_rect)

        for desplazamiento in range(-self.radio + 3, self.radio, 7):
            pygame.draw.circle(
                pantalla,
                self.color,
                (x + desplazamiento, y + self.radio - 1),
                4,
            )

        for desplazamiento in (-6, 6):
            pygame.draw.circle(pantalla, (255, 255, 255), (x + desplazamiento, y - 5), 4)
            pygame.draw.circle(pantalla, (20, 20, 80), (x + desplazamiento, y - 5), 2)


# Molde de la partida entera: ventana, mapa, puntaje y el bucle
class Juego:
    # Abre la ventana, le pone titulo, crea el reloj y dos letras
    # [] es una lista vacia Ahi se van metiendo muros, puntos y fantasmas
    # proximo_umbral_fantasma = 100: el proximo fantasma aparece a los 100 puntos
    # Al final arma el mapa y deja la partida lista con reiniciar
    def __init__(self):
        self.pantalla = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Pac-Man en Pygame")
        self.reloj = pygame.time.Clock()
        self.fuente = pygame.font.SysFont("Arial", 24, bold=True)
        self.fuente_grande = pygame.font.SysFont("Arial", 54, bold=True)
        self.muros = []
        self.puntos = []
        # Las casillas por donde un fantasma puede caminar
        # Error de antes: el fantasma chocaba un rectangulo a 5 pixeles
        # Cambio: pregunta si la casilla de al lado esta en este conjunto
        self.celdas_libres = set()
        self.jugador = None
        self.fantasmas = []
        self.puntaje = 0
        self.game_over = False
        self.juego_completado = False
        self.proximo_umbral_fantasma = 100
        self.historial_jugador = []
        self.ultima_celda_jugador = None
        self.crear_mapa()
        self.reiniciar()

    # El mapa es una tabla de letras
    # "." es pasillo (ahi va un punto) "#" es muro
    # Primero se llena todo con puntos
    # La lista de adentro es una fila La de afuera junta todas las filas
    # El _ del for es una variable que no se va a usar: solo se quiere repetir la accion
    def crear_mapa(self):
        mapa = [["." for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]

        # Pinta el borde range(n) da 0, 1, 2, ... hasta n-1 El ultimo numero no entra
        for fila in range(MAP_HEIGHT):
            mapa[fila][0] = "#"
            mapa[fila][MAP_WIDTH - 1] = "#"
        for columna in range(MAP_WIDTH):
            mapa[0][columna] = "#"
            mapa[MAP_HEIGHT - 1][columna] = "#"

        # Cada tupla es (fila, columna donde empieza, columna donde termina)
        # for fila, inicio, fin in ... separa los tres numeros de cada tupla
        paredes_horizontales = [
            (4, 2, 10), (4, 17, 25),
            (8, 2, 8), (8, 19, 25),
            (12, 2, 10), (12, 17, 25),
            (16, 2, 8), (16, 19, 25),
        ]
        for fila, inicio, fin in paredes_horizontales:
            for columna in range(inicio, fin + 1):
                mapa[fila][columna] = "#"

        # Aca la tupla es (columna, fila inicial, fila final)
        paredes_verticales = [
            (6, 2, 4), (6, 8, 12), (6, 16, 20), (6, 24, 18),
            (21, 2, 4), (21, 8, 12), (21, 16, 20), (21, 24, 18),
        ]
        for columna, inicio, fin in paredes_verticales:
            for fila in range(inicio, fin + 1):
                mapa[fila][columna] = "#"

        # Estas casillas se vuelven a pasar a pasillo para dejar huecos en las paredes
        aperturas = [
            (4, 6), (4, 20), (8, 5), (8, 22),
            (12, 6), (12, 20), (16, 5), (16, 22),
            (10, 6), (10, 21),
        ]
        for fila, columna in aperturas:
            mapa[fila][columna] = "."

        # El centro queda despejado Ahi nacen Pac-Man y el primer fantasma
        # range(9, 13) es 9, 10, 11 y 12 El 13 no entra
        for fila in range(9, 13):
            for columna in range(11, 17):
                mapa[fila][columna] = "."

        # Recorre toda la tabla
        # Si es muro, guarda un rectangulo para los choques
        # Si es pasillo, crea un Punto append lo agrega al final de la lista
        for fila in range(MAP_HEIGHT):
            for columna in range(MAP_WIDTH):
                x = columna * TILE_SIZE
                y = fila * TILE_SIZE
                if mapa[fila][columna] == "#":
                    self.muros.append(pygame.Rect(x, y, TILE_SIZE, TILE_SIZE))
                else:
                    self.puntos.append(Punto(columna, fila))
                    self.celdas_libres.add((columna, fila))

    # Deja la partida como al principio
    # Pac-Man nace en la columna 13, fila 10
    # Hay un solo fantasma, el numero 1
    # Se vuelven a activar todos los puntos
    def reiniciar(self):
        self.puntaje = 0
        self.game_over = False
        self.juego_completado = False
        self.proximo_umbral_fantasma = 100
        self.jugador = Jugador(13, 10)
        # El historial guarda casillas (columna, fila), de la mas vieja a la mas nueva
        # Error de antes: guardaba pixeles, y el verde los seguia en linea recta
        self.historial_jugador = [(13, 10)]
        self.ultima_celda_jugador = (13, 10)
        self.fantasmas = [Fantasma(13, 8, 1)]
        for punto in self.puntos:
            punto.activo = True

    # Suma un fantasma, hasta 6
    # Si ya hay 6, return sale y no hace nada mas
    # Prueba 6 lugares Se queda con los que no caen encima de un muro
    # y elige uno al azar
    # len cuenta cuantos elementos tiene una lista
    # El numero del nuevo es la cantidad actual + 1,
    # asi el segundo recibe la conducta 2, el tercero la 3, y asi
    def agregar_fantasma(self):
        if len(self.fantasmas) >= 6:
            return

        posiciones = [(2, 2), (25, 2), (2, 18), (25, 18), (13, 2), (14, 18)]
        posiciones_disponibles = []
        for columna, fila in posiciones:
            x, y = centro_de_celda(columna, fila)
            rect = pygame.Rect(
                x - TILE_SIZE // 2 + 2,
                y - TILE_SIZE // 2 + 2,
                TILE_SIZE - 4,
                TILE_SIZE - 4,
            )
            if not any(rect.colliderect(muro) for muro in self.muros):
                posiciones_disponibles.append((columna, fila))

        if posiciones_disponibles:
            columna, fila = random.choice(posiciones_disponibles)
            self.fantasmas.append(Fantasma(columna, fila, len(self.fantasmas) + 1))

    # Revisa cada punto que sigue activo
    # continue salta al siguiente punto sin hacer el resto
    # Si Pac-Man esta bastante cerca (un poco mas de media casilla), se lo come:
    # lo apaga y suma 10
    # Cada 100 puntos aparece un fantasma nuevo, hasta 6
    # Al final, all pregunta si todos los puntos estan apagados Si si, se gana
    def recoger_puntos(self):
        for punto in self.puntos:
            if not punto.activo:
                continue
            distancia_al_punto = distancia(
                (self.jugador.x, self.jugador.y),
                (punto.x, punto.y),
            )
            if distancia_al_punto < TILE_SIZE * 0.55:
                punto.activo = False
                self.puntaje += 10
                if (
                    self.puntaje >= self.proximo_umbral_fantasma
                    and len(self.fantasmas) < 6
                ):
                    self.agregar_fantasma()
                    self.proximo_umbral_fantasma += 100

        if all(not punto.activo for punto in self.puntos):
            self.juego_completado = True

    # Si el rectangulo de Pac-Man toca el de un fantasma, se pierde
    # return corta el for: con un choque ya alcanza
    def comprobar_colisiones(self):
        for fantasma in self.fantasmas:
            if self.jugador.rect.colliderect(fantasma.rect):
                self.game_over = True
                return

    # Lee lo que paso desde el fotograma anterior: cerrar la ventana, teclas, etc
    # pygame.event.get() da una lista de eventos y el for los recorre
    def procesar_eventos(self):
        for evento in pygame.event.get():
            # Cerrar la ventana o Escape termina todo
            # pygame.quit apaga el dibujo sys.exit corta Python
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            # Si el evento no es una tecla que se acaba de apretar, se ignora
            if evento.type != pygame.KEYDOWN:
                continue
            if evento.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
            # Si la partida ya termino, solo importa la R para empezar de nuevo
            # continue pasa al siguiente evento y no deja mover a Pac-Man
            if self.game_over or self.juego_completado:
                if evento.key == pygame.K_r:
                    self.reiniciar()
                continue
            # Un diccionario guarda pares La tecla izquierda vale (-1, 0), y asi
            # in pregunta si esa tecla esta entre las flechas
            direcciones = {
                pygame.K_LEFT: (-1, 0),
                pygame.K_RIGHT: (1, 0),
                pygame.K_UP: (0, -1),
                pygame.K_DOWN: (0, 1),
            }
            if evento.key in direcciones:
                self.jugador.establecer_direccion(direcciones[evento.key])

    # La logica de un fotograma Si ya se gano o se perdio, return y no se mueve nada
    def actualizar(self):
        if self.game_over or self.juego_completado:
            return
        self.jugador.actualizar(self.muros)
        # Si Pac-Man cambio de casilla, se agrega al final del rastro
        # [-12:] se queda solo con los ultimos 12 Si no, la lista crece para siempre
        # Ese rastro lo recorre el verde, en orden
        # Error de antes: la cuenta era round(x / 28) y a veces anotaba la casilla de al lado
        celda_jugador = celda_desde_pixel(self.jugador.x, self.jugador.y)
        if celda_jugador != self.ultima_celda_jugador:
            self.historial_jugador.append(celda_jugador)
            self.historial_jugador = self.historial_jugador[-12:]
            self.ultima_celda_jugador = celda_jugador
        for fantasma in self.fantasmas:
            fantasma.actualizar(
                self.celdas_libres,
                self.jugador,
                self.fantasmas,
                self.historial_jugador,
            )
        self.recoger_puntos()
        self.comprobar_colisiones()

    # Pinta cada muro de azul y despues el mismo rectangulo solo con el borde
    # El 1 del final es el grosor de ese borde
    def dibujar_muros(self):
        for muro in self.muros:
            pygame.draw.rect(self.pantalla, COLOR_MURO, muro)
            pygame.draw.rect(self.pantalla, COLOR_MURO_BORDE, muro, 1)

    # La franja de abajo, fuera del mapa
    # f"...{self.puntaje}" arma un texto metiendo el numero dentro de las llaves
    # blit copia ese texto sobre la ventana, en la posicion x, y
    def dibujar_interfaz(self):
        y_interfaz = MAP_HEIGHT * TILE_SIZE
        pygame.draw.rect(
            self.pantalla,
            (15, 15, 45),
            (0, y_interfaz, SCREEN_WIDTH, 70),
        )
        texto_puntaje = self.fuente.render(
            f"Puntaje: {self.puntaje}", True, COLOR_TEXTO
        )
        texto_fantasmas = self.fuente.render(
            f"Fantasmas: {len(self.fantasmas)}/6", True, COLOR_TEXTO
        )
        self.pantalla.blit(texto_puntaje, (20, y_interfaz + 12))
        self.pantalla.blit(
            texto_fantasmas,
            (SCREEN_WIDTH - 180, y_interfaz + 12),
        )
        texto_controles = self.fuente.render(
            "Flechas: mover   ESC: salir", True, (190, 190, 210)
        )
        self.pantalla.blit(texto_controles, (20, y_interfaz + 40))

    # Mientras se esta jugando, las dos condiciones fallan y return sale al toque
    # Si se perdio o se gano, tapa la pantalla con negro medio transparente
    # y escribe el mensaje SRCALPHA deja que el negro sea transparente
    def dibujar_mensaje_final(self):
        if not self.game_over and not self.juego_completado:
            return

        capa = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        capa.fill((0, 0, 0, 180))
        self.pantalla.blit(capa, (0, 0))

        if self.game_over:
            titulo = self.fuente_grande.render("GAME OVER", True, COLOR_ROJO)
        else:
            titulo = self.fuente_grande.render(
                "¡GANASTE!", True, (100, 255, 100)
            )
        subtitulo = self.fuente.render(
            "Presiona R para reiniciar o ESC para salir",
            True,
            COLOR_TEXTO,
        )
        self.pantalla.blit(
            titulo,
            (
                SCREEN_WIDTH // 2 - titulo.get_width() // 2,
                SCREEN_HEIGHT // 2 - 70,
            ),
        )
        self.pantalla.blit(
            subtitulo,
            (
                SCREEN_WIDTH // 2 - subtitulo.get_width() // 2,
                SCREEN_HEIGHT // 2 + 5,
            ),
        )

    # Arma la imagen completa, en este orden
    # Hasta flip(), todo esto esta en memoria y la ventana no cambia
    # flip muestra de una el fotograma que se acaba de armar
    def dibujar(self):
        self.pantalla.fill(COLOR_FONDO)
        self.dibujar_muros()
        for punto in self.puntos:
            punto.dibujar(self.pantalla)
        self.jugador.dibujar(self.pantalla)
        for fantasma in self.fantasmas:
            fantasma.dibujar(self.pantalla)
        self.dibujar_interfaz()
        self.dibujar_mensaje_final()
        pygame.display.flip()

    # while True repite para siempre, hasta que se cierre la ventana o se presione Escape
    # Cada vuelta es un fotograma: esperar, leer teclas, mover, dibujar
    # tick(60) frena lo justo para ir a unos 60 fotogramas por segundo
    def ejecutar(self):
        while True:
            self.reloj.tick(FPS)
            self.procesar_eventos()
            self.actualizar()
            self.dibujar()


# __name__ vale "__main__" solo cuando se corre este archivo directo
# (py pacman.py) Si otro archivo lo inportara, esta parte no corre
# pygame.init enciende pygame
# Juego() dispara el __init__: crea la ventana, el mapa y la partida
# ejecutar entra al while y se queda ahi
# try / finally: aunque algo falle, finally corre igual y cierra pygame
if __name__ == "__main__":
    pygame.init()
    try:
        juego = Juego()
        juego.ejecutar()
    finally:
        pygame.quit()
