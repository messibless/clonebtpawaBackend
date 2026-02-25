# games/serializers.py
from django.utils import timezone 
from rest_framework import serializers
from .models import Game, Match
from datetime import datetime

class MatchSerializer(serializers.ModelSerializer):
    # Tumia match_ref badala ya id
    id = serializers.CharField(source='match_ref', read_only=True)
    
    class Meta:
        model = Match
        fields = ['id', 'teams', 'market', 'selection', 'odds']
        extra_kwargs = {
            'match_ref': {'write_only': True}  # match_ref inakuja kutoka request
        }

class GameResponseSerializer(serializers.ModelSerializer):
    time = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    result = serializers.CharField(default='WON')
    payout = serializers.SerializerMethodField()  # Badilisha kuwa SerializerMethodField
    details = serializers.SerializerMethodField()
    
    class Meta:
        model = Game
        fields = ['id', 'time', 'date', 'result', 'stake', 'odds', 
                 'payout', 'currency', 'details']
    
    def get_time(self, obj):
        return obj.time.strftime("%I:%M %p").lower().lstrip('0')
    
    def get_date(self, obj):
        return obj.date.strftime("%a %d/%m")
    
    def get_payout(self, obj):
        # Hesabu payout: stake * totalOdds
        if obj.stake and obj.total_odds:
            return float(obj.stake) * float(obj.total_odds)
        return 0
    
    def get_details(self, obj):
        matches = obj.matches.all()
        return {
            'matches': MatchSerializer(matches, many=True).data,
            'betType': obj.bet_type,
            'totalOdds': float(obj.total_odds)
        }

class CreateBetSerializer(serializers.Serializer):
    stake = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField(max_length=10, default='TSh')
    matches = serializers.ListField(child=serializers.DictField(), write_only=True)
    
    def validate_matches(self, value):
        if not value:
            raise serializers.ValidationError("At least one match is required")
        return value
    
    def create(self, validated_data):
        matches_data = validated_data.pop('matches')
        
        # Hesabu total odds
        total_odds = 1
        for match in matches_data:
            total_odds *= float(match['odds'])
        
        total_odds = round(total_odds, 2)
        
        # Set active_until (kwa mfano, siku 7 kutoka sasa)
        active_until = timezone.now() + timezone.timedelta(days=7)
        
        # Create game
        game = Game.objects.create(
            stake=validated_data['stake'],
            odds=total_odds,
            currency=validated_data['currency'],
            active_until=active_until,
            bet_type='Accumulator',
            total_odds=total_odds,
            result='WON',  # Weka WON kwa mfano huu
            payout=None  # Tutahesabu kwenye serializer
        )
        
        # Create matches
        for match_data in matches_data:
            Match.objects.create(
                game=game,
                match_ref=match_data['id'],  # "M001", "M002" zinaingia hapa
                teams=match_data['teams'],
                market=match_data['market'],
                selection=match_data['selection'],
                odds=match_data['odds']
            )
        
        return game