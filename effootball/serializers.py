
from rest_framework import serializers
from .models import Efootbal





   
class EfootbalSerializer(serializers.ModelSerializer):

    homeOdds_val = serializers.DecimalField(source='homeOdds', max_digits=10, decimal_places=2, write_only=True)
    drawOdds_val = serializers.DecimalField(source='drawOdds', max_digits=10, decimal_places=2, write_only=True)
    awayOdds_val = serializers.DecimalField(source='awayOdds', max_digits=10, decimal_places=2, write_only=True)

    # These handle the custom JSON structure for the GET response
    homeOdds = serializers.SerializerMethodField(read_only=True)
    drawOdds = serializers.SerializerMethodField(read_only=True)
    awayOdds = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Efootbal
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