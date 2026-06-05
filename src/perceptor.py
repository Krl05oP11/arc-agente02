"""
Módulo 1: PERCEPTOR - Parse grid → WorldState

Convierte representaciones crudas del juego (grids, sprites) en una estructura
de datos simbólica que el resto del agente puede usar.
"""

from src.types import WorldState, Door, Rotator, Teleporter, KeyState
import numpy as np
from typing import Optional, Tuple, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class Perceptor:
    """Analizador que convierte grids crudos en WorldState estructurado"""

    # Tags conocidos del juego (obtenidos del análisis de arc-superagent)
    SPRITE_TAGS = {
        'door': 'rjlbuycveu',
        'refill': 'npxgalaybz',
        'shape_rotator': 'ttfwljgohq',
        'color_rotator': 'soyhouuebz',
        'rot_rotator': 'rhsxkxzdjz',
    }

    # Valores de celda en el grid (observados empiricamente)
    CELL_VALUES = {
        'empty': 0,
        'floor': 3,
        'wall': 4,
        'wall_variant': 5,
    }

    def __init__(self, debug: bool = False):
        """
        Inicializar el Perceptor

        Args:
            debug: Si True, imprimir logs detallados
        """
        self.debug = debug
        if debug:
            logger.setLevel(logging.DEBUG)

    def parse_grid(self, grid: np.ndarray) -> WorldState:
        """
        Parse una grid 64×64 y retorna WorldState

        Args:
            grid: numpy array 64×64 de valores enteros

        Returns:
            WorldState con entidades identificadas

        Raises:
            ValueError: Si la grid no tiene las dimensiones correctas
        """
        if grid.shape != (64, 64):
            raise ValueError(f"Grid debe ser 64×64, got {grid.shape}")

        # Inicializar mundo
        world = WorldState(
            player_pos=(0, 0),  # Placeholder, se actualizará
            walls=set(),
            doors=[],
            rotators=[],
            refills=[],
            teleporters=[],
            key_state=KeyState(shape_id=0, color_id=0, rotation_id=0),  # Placeholder
            energy=42
        )

        # Parse entidades del grid
        self._identify_walls(grid, world)
        self._identify_objects(grid, world)

        if self.debug:
            logger.debug(f"✓ Grid parseado: walls={len(world.walls)}, "
                        f"objects={len(world.doors) + len(world.rotators) + len(world.refills)}")

        return world

    def _identify_walls(self, grid: np.ndarray, world: WorldState) -> None:
        """
        Identificar paredes en el grid

        Las paredes son celdas con valor 4 o 5 (hard walls)
        """
        wall_mask = (grid == 4) | (grid == 5)
        wall_positions = np.argwhere(wall_mask)

        for row, col in wall_positions:
            world.walls.add((int(row), int(col)))

        if self.debug:
            logger.debug(f"✓ Walls: {len(world.walls)} celdas")

    def _identify_objects(self, grid: np.ndarray, world: WorldState) -> None:
        """
        Identificar objetos del juego (doors, rotators, refills, etc.)

        Por ahora, esto es un placeholder que será completado cuando se
        integre con el acceso a sprites del juego real.
        """
        # NOTA: En la implementación final, esto se hará a través de:
        # - level.get_sprites_by_tag() para acceder a sprites por tipo
        # - game.gudziatsk para obtener la posición del player
        # - Análisis de los sprites obtenidos

        if self.debug:
            logger.debug("✓ Objects: Placeholder (sera integrado con game sprites)")

    def extract_key_panel(self, grid: np.ndarray) -> KeyState:
        """
        Extraer estado inicial de la llave del panel UI

        El panel de la llave está en una región fija del grid.
        Para ahora, retorna estado inicial (0,0,0)

        En la implementación final, esto analizará los píxeles del panel
        para determinar la forma, color y rotación actuales de la llave.

        Returns:
            KeyState inicial
        """
        # NOTA: El panel está visible en el grid, pero necesitamos:
        # 1. Extraer los píxeles de la región del panel
        # 2. Analizar los píxeles para determinar forma/color/rot
        # 3. Mapear a índices numéricos

        # Por ahora, retornar placeholder
        return KeyState(shape_id=0, color_id=0, rotation_id=0)

    def identify_entities_from_game(self, game: Any, level: Any) -> Dict[str, Any]:
        """
        Identificar entidades accediendo directamente al objeto Game

        Esto integra con la API del juego real para obtener:
        - Posición del player
        - Localizaciones de doors, rotators, refills, teleporters
        - Estado de la llave

        Args:
            game: Objeto del juego (env._game)
            level: Objeto del nivel (game._levels[index])

        Returns:
            Dict con entidades identificadas
        """
        entities = {
            'player_pos': None,
            'doors': [],
            'rotators': [],
            'refills': [],
            'teleporters': [],
            'key_state': None,
        }

        # Obtener posición del player
        if hasattr(game, 'gudziatsk') and game.gudziatsk:
            player = game.gudziatsk
            entities['player_pos'] = (player.y, player.x)

        # Obtener sprites por tag
        try:
            # Puerta
            doors = level.get_sprites_by_tag(self.SPRITE_TAGS['door'])
            for door in doors:
                entities['doors'].append((door.y, door.x))

            # Refills
            refills = level.get_sprites_by_tag(self.SPRITE_TAGS['refill'])
            for refill in refills:
                entities['refills'].append((refill.y, refill.x))

            # Rotators (SHAPE)
            rotators_shape = level.get_sprites_by_tag(self.SPRITE_TAGS['shape_rotator'])
            for rot in rotators_shape:
                entities['rotators'].append({
                    'pos': (rot.y, rot.x),
                    'type': 'SHAPE',
                    'name': rot.name,
                })

            # Rotators (COLOR)
            rotators_color = level.get_sprites_by_tag(self.SPRITE_TAGS['color_rotator'])
            for rot in rotators_color:
                entities['rotators'].append({
                    'pos': (rot.y, rot.x),
                    'type': 'COLOR',
                    'name': rot.name,
                })

            # Rotators (ROT)
            rotators_rot = level.get_sprites_by_tag(self.SPRITE_TAGS['rot_rotator'])
            for rot in rotators_rot:
                entities['rotators'].append({
                    'pos': (rot.y, rot.x),
                    'type': 'ROT',
                    'name': rot.name,
                })

        except Exception as e:
            if self.debug:
                logger.warning(f"Error al obtener sprites: {e}")

        return entities

    def world_state_from_game(self, grid: np.ndarray, game: Any, level: Any) -> WorldState:
        """
        Crear WorldState completo a partir del grid y el estado del juego

        Combina:
        1. Parse del grid (walls)
        2. Extracción de entidades del game
        3. Estado de la llave

        Args:
            grid: Grid 64×64
            game: Objeto del juego
            level: Objeto del nivel

        Returns:
            WorldState completo
        """
        # Parse grid base
        world = self.parse_grid(grid)

        # Obtener entidades del juego
        entities = self.identify_entities_from_game(game, level)

        # Actualizar world con entidades
        if entities['player_pos']:
            world.player_pos = entities['player_pos']

        # Agregar doors
        for door_pos in entities['doors']:
            # TODO: Extraer el requisito de llave de la puerta
            required_key = KeyState(shape_id=0, color_id=0, rotation_id=0)  # Placeholder
            world.doors.append(Door(position=door_pos, required_key=required_key))

        # Agregar rotators
        for rot_info in entities['rotators']:
            rotator = Rotator(
                position=rot_info['pos'],
                rotator_type=rot_info['type'],
                rotator_id=hash(rot_info['name']) & 0x7fffffff  # Hash del nombre
            )
            world.rotators.append(rotator)

        # Agregar refills
        world.refills = entities['refills']

        # Extraer estado de llave
        world.key_state = self.extract_key_panel(grid)

        return world


def create_perceptor(debug: bool = False) -> Perceptor:
    """Factory para crear un Perceptor"""
    return Perceptor(debug=debug)
