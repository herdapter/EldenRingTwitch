from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
import json
import logging

from .services.elden_parser import EldenRingParser

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class EldenSaveUploadView(View):
    """Vue pour upload et analyse de save Elden Ring"""

    def post(self, request):
        if 'save_file' not in request.FILES:
            return JsonResponse({'error': 'No save file provided'}, status=400)

        save_file = request.FILES['save_file']

        # Validation de base
        if save_file.size > 50 * 1024 * 1024:  # Max 50MB
            return JsonResponse({'error': 'File too large'}, status=400)

        if not save_file.name.endswith('.sl2'):
            return JsonResponse({'error': 'Invalid file type'}, status=400)

        try:
            parser = EldenRingParser()

            # Parse la save
            save_data = parser.parse_save_file(save_file.read())

            # Extrait les personnages
            characters = parser.get_characters(save_data)

            return JsonResponse({
                'success': True,
                'characters': characters,
                'steam_id': save_data.get('global_steam_id', ''),
                'total_slots': len(save_data.get('slots', []))
            })

        except Exception as e:
            logger.error(f"Error parsing save file: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

@require_http_methods(["GET"])
def character_progression(request, slot_index):
    """Récupère la progression détaillée d'un personnage"""

    # Tu devras adapter selon ton système d'auth/session
    # Ici on assume que la save_data est en session ou cache

    try:
        slot_index = int(slot_index)

        # Récupère les données depuis le cache/session
        # save_data = request.session.get('save_data')
        # ou depuis un cache Redis avec un ID utilisateur

        parser = EldenRingParser()
        # progression = parser.get_character_progression(save_data, slot_index)

        # Pour l'exemple, retourne un placeholder
        return JsonResponse({
            'message': 'Implémente la récupération des données selon ton système'
        })

    except ValueError:
        return JsonResponse({'error': 'Invalid slot index'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def parser_health(request):
    """Vérifie le statut du service parser"""

    parser = EldenRingParser()
    is_healthy = parser.health_check()

    return JsonResponse({
        'parser_service': 'healthy' if is_healthy else 'unhealthy',
        'status': 200 if is_healthy else 503
    }, status=200 if is_healthy else 503)