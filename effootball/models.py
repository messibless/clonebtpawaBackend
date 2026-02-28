from django.db import models
from django.utils import timezone
import uuid

def generate_game_id():
    return str(uuid.uuid4().int)[:10]


class Efootbal(models.Model):
    """
    Model for Efootball
    """
    eventId = models.IntegerField(unique=True)
    time = models.TimeField()
    date = models.DateField()
    homeTeam = models.CharField(max_length=100)
    awayTeam = models.CharField(max_length=100)
    league = models.CharField(max_length=200)
    homeOdds = models.DecimalField(max_digits=10, decimal_places=2)  # Hii ni Decimal
    drawOdds = models.DecimalField(max_digits=10, decimal_places=2)  # Hii ni Decimal
    awayOdds = models.DecimalField(max_digits=10, decimal_places=2)  # Hii ni Decimal
    homeOddsFire = models.BooleanField(default=False)  # New field for fire icon
    drawOddsFire = models.BooleanField(default=False)  # New field for fire icon
    awayOddsFire = models.BooleanField(default=False)  # New field for fire icon
    betCount = models.IntegerField(default=0)
    hasBoostedOdds = models.BooleanField(default=False)
    hasTwoUp = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['date', 'time']
    
    def __str__(self):
        return f"{self.homeTeam} vs {self.awayTeam} - {self.league}"