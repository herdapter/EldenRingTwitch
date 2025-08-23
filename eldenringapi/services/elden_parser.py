import requests
import tempfile
import os
import json
import hashlib
import logging
from django.core.cache import cache
from django.conf import settings
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class EldenRingParser:
    """Service pour parser les saves Elden Ring"""

    def __init__(self):
        self.parser_url = getattr(settings, 'ELDEN_PARSER_URL', 'http://localhost:3001')
        self.timeout = getattr(settings, 'ELDEN_PARSER_TIMEOUT', 30)

    def parse_save_file(self, file_content: bytes) -> Dict:
        """Parse un fichier de sauvegarde Elden Ring"""

        # Cache basé sur le hash du fichier
        file_hash = hashlib.md5(file_content).hexdigest()
        cache_key = f"elden_save_{file_hash}"

        try:
            cached_result = cache.get(cache_key)
        except Exception as cache_error:
            cached_result = None
            logger.warning(f"Cache unavailable, proceeding without cache: {cache_error}")

        if cached_result:
            logger.info(f"Cache hit for save file {file_hash[:8]}")
            return cached_result

        logger.info(f"Parsing save file {file_hash[:8]} via service")

        # Parse via le service Node.js
        with tempfile.NamedTemporaryFile(delete=False, suffix='.sl2') as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name

        try:
            with open(temp_file_path, 'rb') as f:
                response = requests.post(
                    f"{self.parser_url}/parse",
                    files={'save_file': ('save.sl2', f, 'application/octet-stream')},
                    timeout=self.timeout
                )

            if response.status_code == 200:
                result = response.json()['data']
                # Cache pendant 1 heure
                try:
                    cache.set(cache_key, result, 3600)
                except Exception as cache_set_error:
                    logger.warning(f"Failed to set cache: {cache_set_error}")
                logger.info(f"Successfully parsed save file {file_hash[:8]}")
                return result
            else:
                error_msg = f"Parser service error {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)

        except requests.RequestException as e:
            error_msg = f"Failed to connect to parser service: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def get_characters(self, save_data: Dict) -> List[Dict]:
        """Extrait la liste des personnages actifs"""

        def decode_character_name(name_array) -> str:
            if not name_array:
                return ""
            try:
                name_bytes = b''.join(int(x).to_bytes(2, 'little') for x in name_array if x != 0)
                return name_bytes.decode('utf-16le').rstrip('\x00')
            except Exception as e:
                logger.warning(f"Failed to decode character name: {e}")
                return "Unknown"

        characters = []
        profile_summaries = save_data.get('profile_summaries', [])

        for i, profile in enumerate(profile_summaries):
            name = decode_character_name(profile.get('character_name', []))
            level = profile.get('level', 0)

            if name and level > 0:
                characters.append({
                    'slot_index': i,
                    'name': name,
                    'level': level
                })

        return characters

    def get_character_progression(self, save_data: Dict, slot_index: int) -> Dict:
        """Analyse la progression d'un personnage"""

        slots = save_data.get('slots', [])
        if slot_index >= len(slots):
            raise ValueError(f"Invalid slot index: {slot_index}")

        slot_data = slots[slot_index]
        player_data = slot_data.get('player_game_data', {})

        # Event flags analysis
        event_flags = slot_data.get('event_flags', {})
        flags_bytes = event_flags.get('flags', [])

        active_flags = 0
        for byte in flags_bytes:
            active_flags += bin(byte).count('1')

        # Regions analysis
        regions = slot_data.get('regions', {})
        unlocked_regions = regions.get('unlocked_regions', [])

        return {
            'character_name': self._decode_player_name(player_data.get('character_name', [])),
            'level': player_data.get('level', 0),
            'souls': player_data.get('souls', 0),
            'stats': {
                'vigor': player_data.get('vigor', 0),
                'mind': player_data.get('mind', 0),
                'endurance': player_data.get('endurance', 0),
                'strength': player_data.get('strength', 0),
                'dexterity': player_data.get('dexterity', 0),
                'intelligence': player_data.get('intelligence', 0),
                'faith': player_data.get('faith', 0),
                'arcane': player_data.get('arcane', 0),
            },
            'progression': {
                'active_flags': active_flags,
                'total_flags': len(flags_bytes) * 8,
                'completion_percentage': (active_flags / (len(flags_bytes) * 8)) * 100 if flags_bytes else 0,
                'unlocked_regions_count': len(unlocked_regions),
                'unlocked_regions': unlocked_regions
            }
        }

    def _decode_player_name(self, name_array) -> str:
        """Helper pour décoder le nom du joueur"""
        if not name_array:
            return ""
        try:
            name_bytes = b''.join(int(x).to_bytes(2, 'little') for x in name_array if x != 0)
            return name_bytes.decode('utf-16le').rstrip('\x00')
        except:
            return "Unknown"

    def health_check(self) -> bool:
        """Vérifie si le service parser est disponible"""
        try:
            response = requests.get(f"{self.parser_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
