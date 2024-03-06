# Std imports
from http import HTTPStatus
import json

# Our own imports
from pong.models import Match, Score
from soninha.models import User

# Django's imports
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils.translation import gettext as _
from django.views.generic import View


def get_matches(user_name):
    """Get matches for a user."""

    matches_list = []
    user = User.objects.get(login_intra=user_name)
    user_matches_query = "SELECT * from pong_score where player_id=" + \
        str(user.id)
    matches_record = Match.objects.raw(user_matches_query)
    for match_record in matches_record:
        scores_query = "SELECT * from pong_score where match_id=" + \
            str(match_record.match_id)
        scores = Score.objects.raw(scores_query)
        left_score = [score for score in scores if score.player_id == user.id]
        right_score = [score for score in scores if score.player_id != user.id]
        match_object = {
            "left_name": user.display_name,
            "left_score": left_score[0].score,
            "right_name": User.objects.get(id=right_score[0].player_id).display_name,
            "right_score": right_score[0].score
        }
        matches_list.append(match_object)
    return matches_list



class MatchView(View):
    """
    This view is responsible for Matches management.
    
    It is called when a new match begins. It creates a new batch in the DB and returns the new match id.

    It is also called after the game ends, and saves the match results and scores in the DB.
    """
    def _validate_incoming_request(self, incoming_request):
        players = incoming_request['players']
        player_quantity = incoming_request['playerQuantity']
        match_type = incoming_request['gameMode']

        if match_type not in [choice[0] for choice in Match.MATCH_TYPE_CHOICES]:
            raise ValueError(_("Invalid game mode: '%(match_type)s'") % {'match_type': match_type})
        if len(players) != player_quantity:
            raise ValueError(_("Fill in the names of all players to start the match."))
        players_set = set(players)
        if len(players_set) != player_quantity:
            raise ValueError(_("Error converting players list to set object"))
        for player in players:
            try:
                User.objects.get(login_intra=player)
            except User.DoesNotExist as e:
                raise ValueError(_("User '%(player)s' does not exist") % {'player': player}) from e

    def post(self, request):
        incoming_request = json.loads(request.body)
        required_params = [
            "gameType",
            "gameMode",
            "playerQuantity",
            "mapSkin",
            "players",
        ]
        for param in required_params:
            if param not in incoming_request:
                return render(request, 'components/errors/player_error.html', {
                    'error_message': _("Missing required parameter: '%(param)s'") % {'param': param}
                }, status=HTTPStatus.BAD_REQUEST)

        try:
            self._validate_incoming_request(incoming_request)
        except (User.DoesNotExist, ValueError) as error:
            return render(request, 'components/errors/player_error.html', {
                'error_message': error
            }, status=HTTPStatus.BAD_REQUEST)

        # Form data is valid at this point, now create a new match and return its id
        new_match = Match.objects.create(type=incoming_request['gameMode'])
        for player in incoming_request['players']:
            user = User.objects.get(login_intra=player)
            Score.objects.create(player=user, match=new_match, score=0)
            new_match.players.add(user)

        response_data = {"match_id": new_match.id}

        return JsonResponse(response_data)

    def put(self, request, *args, **kwargs):
        # TODO: review and test.
        print(f'>> bateu no put')
        print(f'>> [{request}]: request')
        # try:
        #     data = json.loads(request.body)
        #     match_id = data['match_id']
        #     player1_display_name = data['player1']
        #     player2_display_name = data['player2']
        #     player1_score = data['player1_score']
        #     player2_score = data['player2_score']

        #     match_instance = Match.objects.get(pk=match_id)

        #     player1_instance = User.objects.get(
        #         display_name=player1_display_name)
        #     score1 = Score.objects.get(
        #         player=player1_instance, match=match_instance)
        #     score1.score = player1_score
        #     score1.save()

        #     player2_instance = User.objects.get(
        #         display_name=player2_display_name)
        #     score2 = Score.objects.get(
        #         player=player2_instance, match=match_instance)
        #     score2.score = player2_score
        #     score2.save()
        #     # request.session["matches_record"] = get_matches(request.session["intra_login"])
        #     return HttpResponse('')
        # except json.JSONDecodeError:
        #     return HttpResponse('Something went wrong in the Match View')
        return HttpResponse('')
