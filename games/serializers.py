# games/serializers.py
from django.utils import timezone 
from rest_framework import serializers
from .models import Game, Match,Balance, MatchFixture
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
class BalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Balance
        fields = ['id', 'amount', 'currency', 'updated_at', 'created_at']
        read_only_fields = ['id', 'updated_at', 'created_at']
    
    def validate_amount(self, value):
        if value < 0:
            raise serializers.ValidationError("Balance cannot be negative")
        return value
    
    def validate_currency(self, value):
        allowed_currencies = ['TSh', 'USD', 'EUR']
        if value not in allowed_currencies:
            raise serializers.ValidationError(f"Currency must be one of {allowed_currencies}")
        return value
        
class GameResponseSerializer(serializers.ModelSerializer):
    time = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    result = serializers.CharField(default='WON')
    payout = serializers.SerializerMethodField()
    details = serializers.SerializerMethodField()
    status = serializers.CharField()  # 🔥 ONGEZA HII - status field
    
    class Meta:
        model = Game
        fields = ['id', 'time', 'date', 'result', 'stake', 'odds', 
                 'payout', 'currency', 'status', 'details']  # 🔥 ONGEZA 'status' hapa
    
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
        
        # Create game - tumia 'OPEN' badala ya 'WAITING' (kulingana na model yako)
        game = Game.objects.create(
            stake=validated_data['stake'],
            odds=total_odds,
            currency=validated_data['currency'],
            active_until=active_until,
            bet_type='Accumulator',
            total_odds=total_odds,
            result='PENDING',  # Weka PENDING instead of WON
            status='OPEN',  # 🔥 ONGEZA HII - status inapaswa kuwa 'OPEN' not 'WAITING'
            payout=None
        )
        
        # Create matches
        for match_data in matches_data:
            Match.objects.create(
                game=game,
                match_ref=match_data['id'],
                teams=match_data['teams'],
                market=match_data['market'],
                selection=match_data['selection'],
                odds=match_data['odds']
            )
        
        return game
class MatchFixtureSerializer(serializers.ModelSerializer):
    # These fields handle the actual DB values
    # We make them 'write_only' so they don't interfere with our custom output
    homeOdds_val = serializers.DecimalField(source='homeOdds', max_digits=10, decimal_places=2, write_only=True)
    drawOdds_val = serializers.DecimalField(source='drawOdds', max_digits=10, decimal_places=2, write_only=True)
    awayOdds_val = serializers.DecimalField(source='awayOdds', max_digits=10, decimal_places=2, write_only=True)

    # These handle the custom JSON structure for the GET response
    homeOdds = serializers.SerializerMethodField(read_only=True)
    drawOdds = serializers.SerializerMethodField(read_only=True)
    awayOdds = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = MatchFixture
        fields = [
            'id', 'eventId', 'time', 'date', 'homeTeam', 'awayTeam',
            'league', 'homeOdds', 'drawOdds', 'awayOdds', 
            'homeOdds_val', 'drawOdds_val', 'awayOdds_val', # Include write_only fields
            'betCount', 'hasBoostedOdds', 'hasTwoUp'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    # Your existing get_... methods are fine
    def get_homeOdds(self, obj):
        return {'value': str(obj.homeOdds), 'hasFireIcon': obj.homeOddsFire or obj.hasBoostedOdds}

    def get_drawOdds(self, obj):
        return {'value': str(obj.drawOdds), 'hasFireIcon': obj.drawOddsFire}

    def get_awayOdds(self, obj):
        return {'value': str(obj.awayOdds), 'hasFireIcon': obj.awayOddsFire}

    def to_internal_value(self, data):
        """
        Manually map the nested JSON input to the flat model fields
        """
        # Create a mutable copy of the data
        mutable_data = data.copy()

        # Extract values from the nested structure
        for field in ['homeOdds', 'drawOdds', 'awayOdds']:
            val = data.get(field)
            if isinstance(val, dict):
                # Map 'value' to the '..._val' field which points to the DB column
                mutable_data[f'{field}_val'] = val.get('value')
                # Map 'hasFireIcon' to the boolean fields
                mutable_data[f'{field}Fire'] = val.get('hasFireIcon', False)
            else:
                mutable_data[f'{field}_val'] = val

        return super().to_internal_value(mutable_data)