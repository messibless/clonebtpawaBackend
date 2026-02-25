from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import Game, Match
from .serializers import CreateBetSerializer, GameResponseSerializer, MatchSerializer

class BetCRUDView(APIView):
    """
    CRUD operations for Bets using APIView
    """
    
    # ============================================
    # CREATE - POST /api/bets/
    # ============================================
    def post(self, request):
        """Create a new bet"""
        serializer = CreateBetSerializer(data=request.data)
        
        if serializer.is_valid():
            game = serializer.save()
            response_serializer = GameResponseSerializer(game)
            return Response(
                response_serializer.data, 
                status=status.HTTP_201_CREATED
            )
        
        return Response(
            serializer.errors, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # ============================================
    # READ (ALL) - GET /api/bets/
    # ============================================
    def get(self, request):
        """Get all bets or filter by status"""
        # Get query parameters
        status_filter = request.query_params.get('status', None)
        limit = request.query_params.get('limit', None)
        
        # Base queryset
        games = Game.objects.all().order_by('-created_at')
        
        # Apply filters
        if status_filter:
            if status_filter.upper() in ['WAITING', 'SETTLED', 'CANCELLED']:
                games = games.filter(status=status_filter.upper())
        
        # Apply limit
        if limit and limit.isdigit():
            games = games[:int(limit)]
        
        serializer = GameResponseSerializer(games, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BetDetailView(APIView):
    """
    CRUD operations for single bet using APIView
    """
    
    # Helper method to get game or return 404
    def get_object(self, game_id):
        try:
            return Game.objects.get(id=game_id)
        except Game.DoesNotExist:
            return None
    
    # ============================================
    # READ (SINGLE) - GET /api/bets/<id>/
    # ============================================
    def get(self, request, game_id):
        """Get a single bet by ID"""
        game = self.get_object(game_id)
        
        if not game:
            return Response(
                {'error': 'Game not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = GameResponseSerializer(game)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # ============================================
    # UPDATE (FULL) - PUT /api/bets/<id>/
    # ============================================
    def put(self, request, game_id):
        """Update entire bet"""
        game = self.get_object(game_id)
        
        if not game:
            return Response(
                {'error': 'Game not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = CreateBetSerializer(game, data=request.data)
        
        if serializer.is_valid():
            updated_game = serializer.save()
            response_serializer = GameResponseSerializer(updated_game)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        
        return Response(
            serializer.errors, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # ============================================
    # UPDATE (PARTIAL) - PATCH /api/bets/<id>/
    # ============================================
    def patch(self, request, game_id):
        """Partially update a bet"""
        game = self.get_object(game_id)
        
        if not game:
            return Response(
                {'error': 'Game not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = CreateBetSerializer(game, data=request.data, partial=True)
        
        if serializer.is_valid():
            updated_game = serializer.save()
            response_serializer = GameResponseSerializer(updated_game)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        
        return Response(
            serializer.errors, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # ============================================
    # DELETE - DELETE /api/bets/<id>/
    # ============================================
    def delete(self, request, game_id):
        """Delete a bet"""
        game = self.get_object(game_id)
        
        if not game:
            return Response(
                {'error': 'Game not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Store info before deletion
        game_info = {
            'id': game.id,
            'message': f'Game {game.id} deleted successfully'
        }
        
        game.delete()
        
        return Response(game_info, status=status.HTTP_200_OK)


class BetApproveView(APIView):
    """
    Special view for approving/settling bets
    """
    
    def post(self, request, game_id):
        """Approve/settle a bet"""
        try:
            game = Game.objects.get(id=game_id)
        except Game.DoesNotExist:
            return Response(
                {'error': 'Game not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if game can be settled
        if game.status != 'WAITING':
            return Response({
                'error': f'Game cannot be settled. Current status: {game.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if game is still active
        if game.active_until < timezone.now():
            return Response({
                'error': 'Game has expired. Cannot settle.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get result from request
        result = request.data.get('result', 'LOST')
        
        # Update game
        game.result = result
        game.status = 'SETTLED'
        game.settled_at = timezone.now()
        
        # Calculate payout
        if result == 'WON':
            game.payout = game.stake * game.odds
        else:
            game.payout = 0
        
        game.save()
        
        serializer = GameResponseSerializer(game)
        return Response({
            'message': 'Game approved successfully',
            'game': serializer.data
        }, status=status.HTTP_200_OK)


class BetFilterView(APIView):
    """
    View for filtered bet lists
    """
    
    def get(self, request):
        """Get filtered bets"""
        # Get all active (waiting) games
        active_games = Game.objects.filter(
            status='WAITING', 
            active_until__gte=timezone.now()
        ).order_by('-created_at')
        
        # Get all settled games
        settled_games = Game.objects.filter(
            status='SETTLED'
        ).order_by('-created_at')
        
        # Get recent games (last 10)
        recent_games = Game.objects.all().order_by('-created_at')[:10]
        
        data = {
            'active': GameResponseSerializer(active_games, many=True).data,
            'settled': GameResponseSerializer(settled_games, many=True).data,
            'recent': GameResponseSerializer(recent_games, many=True).data,
            'counts': {
                'total': Game.objects.count(),
                'active': active_games.count(),
                'settled': settled_games.count(),
                'pending': Game.objects.filter(result='PENDING').count(),
                'won': Game.objects.filter(result='WON').count(),
                'lost': Game.objects.filter(result='LOST').count()
            }
        }
        
        return Response(data, status=status.HTTP_200_OK)


class MatchCRUDView(APIView):
    """
    CRUD operations for matches
    """
    
    # ============================================
    # ADD MATCH TO GAME - POST /api/bets/<game_id>/matches/
    # ============================================
    def post(self, request, game_id):
        """Add a match to a game"""
        try:
            game = Game.objects.get(id=game_id)
        except Game.DoesNotExist:
            return Response(
                {'error': 'Game not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if game can be modified
        if game.status != 'WAITING':
            return Response({
                'error': 'Cannot add matches to a settled or cancelled game'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = MatchSerializer(data=request.data)
        
        if serializer.is_valid():
            match = serializer.save(game=game)
            
            # Recalculate total odds
            self.recalculate_game_odds(game)
            
            return Response(
                MatchSerializer(match).data, 
                status=status.HTTP_201_CREATED
            )
        
        return Response(
            serializer.errors, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # ============================================
    # UPDATE MATCH - PUT /api/matches/<match_id>/
    # ============================================
    def put(self, request, match_id):
        """Update a match"""
        try:
            match = Match.objects.get(id=match_id)
        except Match.DoesNotExist:
            return Response(
                {'error': 'Match not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if game can be modified
        if match.game.status != 'WAITING':
            return Response({
                'error': 'Cannot update matches of a settled or cancelled game'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = MatchSerializer(match, data=request.data)
        
        if serializer.is_valid():
            updated_match = serializer.save()
            
            # Recalculate game odds
            self.recalculate_game_odds(match.game)
            
            return Response(
                MatchSerializer(updated_match).data, 
                status=status.HTTP_200_OK
            )
        
        return Response(
            serializer.errors, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # ============================================
    # DELETE MATCH - DELETE /api/matches/<match_id>/
    # ============================================
    def delete(self, request, match_id):
        """Delete a match"""
        try:
            match = Match.objects.get(id=match_id)
        except Match.DoesNotExist:
            return Response(
                {'error': 'Match not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if game can be modified
        if match.game.status != 'WAITING':
            return Response({
                'error': 'Cannot delete matches from a settled or cancelled game'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        game = match.game
        match_info = {
            'id': match.id,
            'match_ref': match.match_ref,
            'message': f'Match deleted successfully'
        }
        
        match.delete()
        
        # Recalculate game odds if matches remain
        self.recalculate_game_odds(game)
        
        return Response(match_info, status=status.HTTP_200_OK)
    
    def recalculate_game_odds(self, game):
        """Helper method to recalculate game total odds"""
        matches = game.matches.all()
        
        if matches.exists():
            total_odds = 1
            for match in matches:
                total_odds *= float(match.odds)
            
            game.odds = round(total_odds, 2)
            game.total_odds = round(total_odds, 2)
        else:
            game.odds = 0
            game.total_odds = 0
        
        game.save()