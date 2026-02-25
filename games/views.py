from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import Game, Match,Balance, MatchFixture
from .serializers import CreateBetSerializer,BalanceSerializer, GameResponseSerializer, MatchSerializer, MatchFixtureSerializer




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
            if status_filter.upper() in ['OPEN', 'SETTLED']:
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
        
        # Check if game can be settled - using 'OPEN' from model
        if game.status != 'OPEN':
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
        # Get all active (OPEN) games
        active_games = Game.objects.filter(
            status='OPEN', 
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
        
        # Check if game can be modified - using 'OPEN'
        if game.status != 'OPEN':
            return Response({
                'error': 'Cannot add matches to a settled game'
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
        
        # Check if game can be modified - using 'OPEN'
        if match.game.status != 'OPEN':
            return Response({
                'error': 'Cannot update matches of a settled game'
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
        
        # Check if game can be modified - using 'OPEN'
        if match.game.status != 'OPEN':
            return Response({
                'error': 'Cannot delete matches from a settled game'
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


class AccountBalanceView(APIView):
    """
    View to manage account balance with database persistence
    """
    
    def get_balance_object(self):
        """Get or create the single balance record"""
        balance = Balance.objects.first()
        if not balance:
            balance = Balance.objects.create(amount=0.00, currency='TSh')
        return balance
    
    def get(self, request):
        """Get current account balance"""
        balance = self.get_balance_object()
        serializer = BalanceSerializer(balance)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        """Create account balance (only works if no balance exists)"""
        if Balance.objects.exists():
            return Response({
                'error': 'Balance already exists. Use PUT to update.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = BalanceSerializer(data=request.data)
        if serializer.is_valid():
            balance = serializer.save()
            return Response({
                'message': 'Balance created successfully',
                'data': BalanceSerializer(balance).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request):
        """Update account balance"""
        balance = self.get_balance_object()
        serializer = BalanceSerializer(balance, data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Balance updated successfully',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request):
        """Partially update account balance"""
        balance = self.get_balance_object()
        serializer = BalanceSerializer(balance, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Balance updated successfully',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

 

class MatchFixtureListCreateView(APIView):
    """
    View to list and create match fixtures
    """
    
    def get(self, request):
        """Get all match fixtures"""
        fixtures = MatchFixture.objects.all().order_by('date', 'time')
        serializer = MatchFixtureSerializer(fixtures, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        """Create a new match fixture"""
        print("📥 Received data:", request.data)  # Debug print
        
        serializer = MatchFixtureSerializer(data=request.data)
        
        if serializer.is_valid():
            fixture = serializer.save()
            print("✅ Created fixture:", fixture.id)
            return Response(
                MatchFixtureSerializer(fixture).data,
                status=status.HTTP_201_CREATED
            )
        
        print("❌ Serializer errors:", serializer.errors)  # Debug print
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MatchFixtureDetailView(APIView):
    """
    View to retrieve, update or delete a match fixture
    """
    
    def get_object(self, pk):
        try:
            return MatchFixture.objects.get(pk=pk)
        except MatchFixture.DoesNotExist:
            return None
    
    # ============================================
    # GET single fixture - /api/fixtures/<id>/
    # ============================================
    def get(self, request, pk):
        """Get a single match fixture by ID"""
        fixture = self.get_object(pk)
        
        if not fixture:
            return Response(
                {'error': 'Match fixture not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = MatchFixtureSerializer(fixture)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # ============================================
    # UPDATE full fixture - PUT /api/fixtures/<id>/
    # ============================================
    def put(self, request, pk):
        """Update entire match fixture"""
        fixture = self.get_object(pk)
        
        if not fixture:
            return Response(
                {'error': 'Match fixture not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        print(f"📥 Updating fixture {pk} with data:", request.data)
        
        serializer = MatchFixtureSerializer(fixture, data=request.data)
        
        if serializer.is_valid():
            updated_fixture = serializer.save()
            print(f"✅ Updated fixture {pk}")
            return Response(
                MatchFixtureSerializer(updated_fixture).data,
                status=status.HTTP_200_OK
            )
        
        print("❌ Update errors:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # ============================================
    # PARTIAL UPDATE - PATCH /api/fixtures/<id>/
    # ============================================
    def patch(self, request, pk):
        """Partially update a match fixture"""
        fixture = self.get_object(pk)
        
        if not fixture:
            return Response(
                {'error': 'Match fixture not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        print(f"📥 Partially updating fixture {pk} with data:", request.data)
        
        serializer = MatchFixtureSerializer(fixture, data=request.data, partial=True)
        
        if serializer.is_valid():
            updated_fixture = serializer.save()
            print(f"✅ Partially updated fixture {pk}")
            return Response(
                MatchFixtureSerializer(updated_fixture).data,
                status=status.HTTP_200_OK
            )
        
        print("❌ Partial update errors:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # ============================================
    # DELETE - DELETE /api/fixtures/<id>/
    # ============================================
    def delete(self, request, pk):
        """Delete a match fixture"""
        fixture = self.get_object(pk)
        
        if not fixture:
            return Response(
                {'error': 'Match fixture not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        fixture_info = {
            'id': fixture.id,
            'eventId': fixture.eventId,
            'message': f'Fixture {fixture.id} - {fixture.homeTeam} vs {fixture.awayTeam} deleted successfully'
        }
        
        fixture.delete()
        print(f"✅ Deleted fixture {pk}")
        
        return Response(fixture_info, status=status.HTTP_200_OK)


class MatchFixtureBulkCreateView(APIView):
    """
    View to create multiple match fixtures at once
    """
    
    def post(self, request):
        """Create multiple match fixtures"""
        print("📥 Bulk create received:", len(request.data) if isinstance(request.data, list) else "Not a list")
        
        if not isinstance(request.data, list):
            return Response(
                {'error': 'Expected a list of fixtures'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_fixtures = []
        errors = []
        
        for index, fixture_data in enumerate(request.data):
            print(f"Processing fixture {index}:", fixture_data)
            serializer = MatchFixtureSerializer(data=fixture_data)
            if serializer.is_valid():
                fixture = serializer.save()
                created_fixtures.append(MatchFixtureSerializer(fixture).data)
                print(f"✅ Created fixture {index}")
            else:
                errors.append({
                    'index': index,
                    'data': fixture_data,
                    'errors': serializer.errors
                })
                print(f"❌ Error in fixture {index}:", serializer.errors)
        
        response_data = {
            'created': created_fixtures,
            'errors': errors,
            'total_created': len(created_fixtures),
            'total_errors': len(errors)
        }
        
        status_code = status.HTTP_201_CREATED if created_fixtures else status.HTTP_400_BAD_REQUEST
        return Response(response_data, status=status_code)
   


class MatchFixtureBulkUpdateView(APIView):
    """
    View to update multiple match fixtures at once
    """
    
    def put(self, request):
        """Update multiple match fixtures"""
        print("📥 Bulk update received:", len(request.data) if isinstance(request.data, list) else "Not a list")
        
        if not isinstance(request.data, list):
            return Response(
                {'error': 'Expected a list of fixtures with ids'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        updated_fixtures = []
        errors = []
        
        for index, fixture_data in enumerate(request.data):
            fixture_id = fixture_data.get('id')
            
            if not fixture_id:
                errors.append({
                    'index': index,
                    'data': fixture_data,
                    'errors': {'id': 'This field is required for updates'}
                })
                continue
            
            try:
                fixture = MatchFixture.objects.get(pk=fixture_id)
                serializer = MatchFixtureSerializer(fixture, data=fixture_data)
                
                if serializer.is_valid():
                    updated_fixture = serializer.save()
                    updated_fixtures.append(MatchFixtureSerializer(updated_fixture).data)
                    print(f"✅ Updated fixture {fixture_id}")
                else:
                    errors.append({
                        'index': index,
                        'id': fixture_id,
                        'data': fixture_data,
                        'errors': serializer.errors
                    })
                    print(f"❌ Error updating fixture {fixture_id}:", serializer.errors)
                    
            except MatchFixture.DoesNotExist:
                errors.append({
                    'index': index,
                    'id': fixture_id,
                    'data': fixture_data,
                    'errors': {'id': f'Fixture with id {fixture_id} not found'}
                })
        
        response_data = {
            'updated': updated_fixtures,
            'errors': errors,
            'total_updated': len(updated_fixtures),
            'total_errors': len(errors)
        }
        
        status_code = status.HTTP_200_OK if updated_fixtures else status.HTTP_400_BAD_REQUEST
        return Response(response_data, status=status_code)


class MatchFixtureBulkDeleteView(APIView):
    """
    View to delete multiple match fixtures at once
    """
    
    def delete(self, request):
        """Delete multiple match fixtures"""
        fixture_ids = request.data.get('ids', [])
        
        if not fixture_ids:
            return Response(
                {'error': 'Expected a list of fixture ids'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        deleted = []
        not_found = []
        
        for fixture_id in fixture_ids:
            try:
                fixture = MatchFixture.objects.get(pk=fixture_id)
                fixture_info = {
                    'id': fixture.id,
                    'eventId': fixture.eventId,
                    'homeTeam': fixture.homeTeam,
                    'awayTeam': fixture.awayTeam
                }
                fixture.delete()
                deleted.append(fixture_info)
                print(f"✅ Deleted fixture {fixture_id}")
            except MatchFixture.DoesNotExist:
                not_found.append(fixture_id)
                print(f"❌ Fixture {fixture_id} not found")
        
        response_data = {
            'deleted': deleted,
            'not_found': not_found,
            'total_deleted': len(deleted),
            'total_not_found': len(not_found)
        }
        
        status_code = status.HTTP_200_OK if deleted else status.HTTP_404_NOT_FOUND
        return Response(response_data, status=status_code)