import math
import random
import sys

import pygame


TILE_SIZE = 28
MAP_WIDTH = 28
MAP_HEIGHT = 21

SCREEN_WIDTH = MAP_WIDTH * TILE_SIZE
SCREEN_HEIGHT = MAP_HEIGHT * TILE_SIZE + 70
FPS = 60

COLOR_FONDO = (5, 5, 25)
COLOR_MURO = (25, 45, 180)
COLOR_MURO_BORDE = (80, 110, 255)
COLOR_JUGADOR = (255, 230, 0)
COLOR_PUNTO = (255, 220, 150)
COLOR_TEXTO = (255, 255, 255)
COLOR_ROJO = (255, 60, 60)


def distancia(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def centro_de_celda(columna, fila):
    return (
        columna * TILE_SIZE + TILE_SIZE // 2,
        fila * TILE_SIZE + TILE_SIZE // 2,
    )


class Punto:
    def __init__(self, columna, fila):
        self.columna = columna
        self.fila = fila
        self.x, self.y = centro_de_celda(columna, fila)
        self.radio = 4
        self.activo = True

    def dibujar(self, pantalla):
        if self.activo:
            pygame.draw.circle(pantalla, COLOR_PUNTO, (self.x, self.y), self.radio)


class Jugador:
    def __init__(self, columna, fila):
        self.x, self.y = centro_de_celda(columna, fila)
        self.radio = TILE_SIZE // 2 - 3
        self.velocidad = 3
        self.direccion = (0, 0)
        self.direccion_solicitada = (0, 0)
        self.rect = pygame.Rect(0, 0, self.radio * 2, self.radio * 2)
        self.actualizar_rectangulo()

    def actualizar_rectangulo(self):
        self.rect.center = (round(self.x), round(self.y))

    def establecer_direccion(self, direccion):
        self.direccion_solicitada = direccion

    def puede_moverse(self, dx, dy, muros):
        prueba = self.rect.copy()
        prueba.center = (round(self.x + dx), round(self.y + dy))
        return not any(prueba.colliderect(muro) for muro in muros)

    def actualizar(self, muros):
        dx_solicitada, dy_solicitada = self.direccion_solicitada
        if self.puede_moverse(
            dx_solicitada * self.velocidad,
            dy_solicitada * self.velocidad,
            muros,
        ):
            self.direccion = self.direccion_solicitada

        dx, dy = self.direccion
        movimiento_x = dx * self.velocidad
        movimiento_y = dy * self.velocidad

        if self.puede_moverse(movimiento_x, movimiento_y, muros):
            self.x += movimiento_x
            self.y += movimiento_y
        else:
            self.direccion = (0, 0)

        self.actualizar_rectangulo()

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


class Fantasma:
    COLORES = [
        (255, 50, 50),
        (255, 140, 255),
        (0, 230, 255),
        (255, 150, 0),
        (100, 255, 100),
        (180, 100, 255),
    ]
    DIRECCIONES = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    def __init__(self, columna, fila, numero):
        self.x, self.y = centro_de_celda(columna, fila)
        self.numero = numero
        self.color = self.COLORES[(numero - 1) % len(self.COLORES)]
        self.radio = TILE_SIZE // 2 - 3
        self.velocidad = 1.8 + (numero - 1) * 0.08
        self.direccion = random.choice(self.DIRECCIONES)
        self.rect = pygame.Rect(0, 0, self.radio * 2, self.radio * 2)
        self.actualizar_rectangulo()

    def actualizar_rectangulo(self):
        self.rect.center = (round(self.x), round(self.y))

    def esta_cerca_del_centro(self):
        centro_x = round(self.x / TILE_SIZE) * TILE_SIZE
        centro_y = round(self.y / TILE_SIZE) * TILE_SIZE
        return (
            abs(self.x - centro_x) < self.velocidad + 0.5
            and abs(self.y - centro_y) < self.velocidad + 0.5
        )

    def puede_moverse(self, direccion, muros):
        dx, dy = direccion
        prueba = self.rect.copy()
        prueba.center = (
            round(self.x + dx * self.velocidad * 3),
            round(self.y + dy * self.velocidad * 3),
        )
        return not any(prueba.colliderect(muro) for muro in muros)

    def direcciones_validas(self, muros):
        return [
            direccion
            for direccion in self.DIRECCIONES
            if self.puede_moverse(direccion, muros)
        ]

    def objetivo(self, jugador, fantasmas, historial_jugador):
        if self.numero == 1:
            return jugador.x, jugador.y

        if self.numero == 2:
            dx, dy = jugador.direccion
            return (
                jugador.x + dx * TILE_SIZE * 4,
                jugador.y + dy * TILE_SIZE * 4,
            )

        if self.numero == 3:
            dx, dy = jugador.direccion
            objetivo_del_segundo = (
                jugador.x + dx * TILE_SIZE * 2,
                jugador.y + dy * TILE_SIZE * 2,
            )
            primero = fantasmas[0]
            return (
                objetivo_del_segundo[0]
                + (objetivo_del_segundo[0] - primero.x),
                objetivo_del_segundo[1]
                + (objetivo_del_segundo[1] - primero.y),
            )

        if self.numero == 4:
            if distancia((self.x, self.y), (jugador.x, jugador.y)) < TILE_SIZE * 8:
                esquinas = [
                    (TILE_SIZE * 2, TILE_SIZE * 2),
                    ((MAP_WIDTH - 3) * TILE_SIZE, TILE_SIZE * 2),
                    (TILE_SIZE * 2, (MAP_HEIGHT - 3) * TILE_SIZE),
                    (
                        (MAP_WIDTH - 3) * TILE_SIZE,
                        (MAP_HEIGHT - 3) * TILE_SIZE,
                    ),
                ]
                return max(
                    esquinas,
                    key=lambda esquina: distancia(
                        (self.x, self.y), esquina
                    ),
                )
            return jugador.x, jugador.y

        if self.numero == 5 and historial_jugador:
            return historial_jugador[0]

        return None

    def elegir_direccion(self, muros, jugador, fantasmas, historial_jugador):
        validas = self.direcciones_validas(muros)
        if not validas:
            self.direccion = (-self.direccion[0], -self.direccion[1])
            return

        if self.numero == 6:
            self.direccion = random.choice(validas)
            return

        objetivo = self.objetivo(jugador, fantasmas, historial_jugador)
        if objetivo is None:
            self.direccion = random.choice(validas)
            return

        mejor_direccion = None
        mejor_distancia = float("inf")
        for direccion in validas:
            dx, dy = direccion
            posible_x = self.x + dx * TILE_SIZE
            posible_y = self.y + dy * TILE_SIZE
            distancia_al_objetivo = distancia(
                (posible_x, posible_y), objetivo
            )
            if distancia_al_objetivo < mejor_distancia:
                mejor_distancia = distancia_al_objetivo
                mejor_direccion = direccion

        self.direccion = mejor_direccion or random.choice(validas)

    def actualizar(self, muros, jugador, fantasmas, historial_jugador):
        if self.esta_cerca_del_centro():
            self.elegir_direccion(
                muros, jugador, fantasmas, historial_jugador
            )

        dx, dy = self.direccion
        if self.puede_moverse(self.direccion, muros):
            self.x += dx * self.velocidad
            self.y += dy * self.velocidad
        else:
            self.elegir_direccion(
                muros, jugador, fantasmas, historial_jugador
            )

        self.actualizar_rectangulo()

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


class Juego:
    def __init__(self):
        self.pantalla = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Pac-Man en Pygame")
        self.reloj = pygame.time.Clock()
        self.fuente = pygame.font.SysFont("Arial", 24, bold=True)
        self.fuente_grande = pygame.font.SysFont("Arial", 54, bold=True)
        self.muros = []
        self.puntos = []
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

    def crear_mapa(self):
        mapa = [["." for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]

        for fila in range(MAP_HEIGHT):
            mapa[fila][0] = "#"
            mapa[fila][MAP_WIDTH - 1] = "#"
        for columna in range(MAP_WIDTH):
            mapa[0][columna] = "#"
            mapa[MAP_HEIGHT - 1][columna] = "#"

        paredes_horizontales = [
            (4, 2, 10), (4, 17, 25),
            (8, 2, 8), (8, 19, 25),
            (12, 2, 10), (12, 17, 25),
            (16, 2, 8), (16, 19, 25),
        ]
        for fila, inicio, fin in paredes_horizontales:
            for columna in range(inicio, fin + 1):
                mapa[fila][columna] = "#"

        paredes_verticales = [
            (6, 2, 4), (6, 8, 12), (6, 16, 20), (6, 24, 18),
            (21, 2, 4), (21, 8, 12), (21, 16, 20), (21, 24, 18),
        ]
        for columna, inicio, fin in paredes_verticales:
            for fila in range(inicio, fin + 1):
                mapa[fila][columna] = "#"

        aperturas = [
            (4, 6), (4, 20), (8, 5), (8, 22),
            (12, 6), (12, 20), (16, 5), (16, 22),
            (10, 6), (10, 21),
        ]
        for fila, columna in aperturas:
            mapa[fila][columna] = "."

        for fila in range(9, 13):
            for columna in range(11, 17):
                mapa[fila][columna] = "."

        for fila in range(MAP_HEIGHT):
            for columna in range(MAP_WIDTH):
                x = columna * TILE_SIZE
                y = fila * TILE_SIZE
                if mapa[fila][columna] == "#":
                    self.muros.append(pygame.Rect(x, y, TILE_SIZE, TILE_SIZE))
                else:
                    self.puntos.append(Punto(columna, fila))

    def reiniciar(self):
        self.puntaje = 0
        self.game_over = False
        self.juego_completado = False
        self.proximo_umbral_fantasma = 100
        self.jugador = Jugador(13, 10)
        self.historial_jugador = [(
            self.jugador.x,
            self.jugador.y,
        )]
        self.ultima_celda_jugador = (13, 10)
        self.fantasmas = [Fantasma(13, 8, 1)]
        for punto in self.puntos:
            punto.activo = True

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

    def comprobar_colisiones(self):
        for fantasma in self.fantasmas:
            if self.jugador.rect.colliderect(fantasma.rect):
                self.game_over = True
                return

    def procesar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type != pygame.KEYDOWN:
                continue
            if evento.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
            if self.game_over or self.juego_completado:
                if evento.key == pygame.K_r:
                    self.reiniciar()
                continue
            direcciones = {
                pygame.K_LEFT: (-1, 0),
                pygame.K_RIGHT: (1, 0),
                pygame.K_UP: (0, -1),
                pygame.K_DOWN: (0, 1),
            }
            if evento.key in direcciones:
                self.jugador.establecer_direccion(direcciones[evento.key])

    def actualizar(self):
        if self.game_over or self.juego_completado:
            return
        self.jugador.actualizar(self.muros)
        celda_jugador = (
            round(self.jugador.x / TILE_SIZE),
            round(self.jugador.y / TILE_SIZE),
        )
        if celda_jugador != self.ultima_celda_jugador:
            self.historial_jugador.append(centro_de_celda(*celda_jugador))
            self.historial_jugador = self.historial_jugador[-12:]
            self.ultima_celda_jugador = celda_jugador
        for fantasma in self.fantasmas:
            fantasma.actualizar(
                self.muros,
                self.jugador,
                self.fantasmas,
                self.historial_jugador,
            )
        self.recoger_puntos()
        self.comprobar_colisiones()

    def dibujar_muros(self):
        for muro in self.muros:
            pygame.draw.rect(self.pantalla, COLOR_MURO, muro)
            pygame.draw.rect(self.pantalla, COLOR_MURO_BORDE, muro, 1)

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

    def ejecutar(self):
        while True:
            self.reloj.tick(FPS)
            self.procesar_eventos()
            self.actualizar()
            self.dibujar()


if __name__ == "__main__":
    pygame.init()
    try:
        juego = Juego()
        juego.ejecutar()
    finally:
        pygame.quit()
