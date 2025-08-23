import os
import json
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from eldenringapi.services.elden_parser import EldenRingParser
from .models import GameData, TwitchSession

@shared_task(bind=True)
def analyze_save_file(self, file_path: str, session_code: str):
    parser = EldenRingParser()
    try:
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}

        with open(file_path, "rb") as f:
            file_content = f.read()

        parsed = parser.parse_save_file(file_content)

        # Build meaningful summaries from parsed data
        map_discovered = {}
        bosses_defeated = {}

        try:
            # Lazy-load event flag mappings
            event_flags_path = os.path.join(settings.BASE_DIR, 'event_flags.json')
            with open(event_flags_path, 'r') as f:
                flags_config = json.load(f)
            event_flags_map = flags_config.get('event_flags', {})
            boss_names = flags_config.get('boss_names', {})
            map_names = flags_config.get('map_names', {})

            def is_flag_set(flags_dict: dict, event_id: str) -> bool:
                mapping = event_flags_map.get(str(event_id))
                if not mapping:
                    return False
                group, bit = mapping
                value = flags_dict.get(str(group))
                if isinstance(value, int):
                    return ((value >> bit) & 1) == 1
                if isinstance(value, str):
                    try:
                        iv = int(value)
                        return ((iv >> bit) & 1) == 1
                    except Exception:
                        return False
                return False

            characters = parser.get_characters(parsed)

            # Fallback: if no characters detected, try slot 0
            if not characters:
                slots = parsed.get("slots", [])
                if slots:
                    characters = [{"slot_index": 0, "name": "slot_0"}]

            for character in characters:
                slot_index = character.get("slot_index", 0)
                character_name = character.get("name") or f"slot_{slot_index}"

                # Extract event flags and regions for this slot without relying on progression helper
                slot_obj = parsed.get('slots', [])[slot_index]
                flags_dict = {}
                try:
                    flags_dict = slot_obj.get('event_flags', {}).get('flags', {})
                    if not isinstance(flags_dict, dict):
                        flags_dict = {}
                except Exception:
                    flags_dict = {}

                regions_obj = slot_obj.get('regions', {}) if isinstance(slot_obj, dict) else {}
                unlocked_regions = regions_obj.get('unlocked_regions', []) if isinstance(regions_obj, dict) else []

                # Compute acquired maps and defeated bosses from flags
                acquired_maps = [name for eid, name in map_names.items() if is_flag_set(flags_dict, eid)]
                defeated_bosses = [name for eid, name in boss_names.items() if is_flag_set(flags_dict, eid)]

                map_discovered[character_name] = {
                    "unlocked_regions_count": len(unlocked_regions),
                    "unlocked_regions": unlocked_regions,
                    "completion_percentage": 0,
                    "acquired_maps": acquired_maps,
                    "acquired_maps_count": len(acquired_maps),
                }

                bosses_defeated[character_name] = {
                    "defeated_bosses": defeated_bosses,
                    "defeated_bosses_count": len(defeated_bosses),
                }
        except Exception:
            # Fallback to empty structures if mapping fails
            map_discovered = {}
            bosses_defeated = {}

        with transaction.atomic():
            session_obj, _ = TwitchSession.objects.get_or_create(code=session_code)
            GameData.objects.update_or_create(
                twitch_id=session_obj,
                defaults={
                    "map_discovered": map_discovered,
                    "bosses_defeated": bosses_defeated,
                    "last_updated": timezone.now(),
                },
            )

        return {"success": True}

    except Exception as e:
        return {"error": str(e)}

    finally:
        # Do not delete the original file_path; the parser manages its own temp files.
        pass
