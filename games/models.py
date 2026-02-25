# games/models.py

from django.db import models
from django.utils import timezone
import uuid

def generate_game_id():
    return str(uuid.uuid4().int)[:10]

class Game(models.Model):
    GAME_STATUS = (
        ('OPEN', 'Open'),
        ('SETTLED', 'Settled'),
    )
    
    RESULT_CHOICES = (
        ('WON', 'Won'),
        ('LOST', 'Lost'),
        ('PENDING', 'Pending'),
    )
    
    id = models.CharField(max_length=20, primary_key=True, default=generate_game_id)
    time = models.TimeField(auto_now_add=True)
    date = models.DateField(auto_now_add=True)
    result = models.CharField(max_length=10, choices=RESULT_CHOICES, default='PENDING')
    stake = models.DecimalField(max_digits=10, decimal_places=2)
    odds = models.DecimalField(max_digits=10, decimal_places=2)
    payout = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, default='TSh')
    status = models.CharField(max_length=10, choices=GAME_STATUS, default='OPEN')
    active_until = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    settled_at = models.DateTimeField(null=True, blank=True)
    bet_type = models.CharField(max_length=20, default='Accumulator')
    total_odds = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"Game {self.id} - {self.status}"
    
    def approve_game(self):
        self.status = 'SETTLED'
        self.settled_at = timezone.now()
        if self.result == 'WON':
            self.payout = self.stake * self.odds
        else:
            self.payout = 0
        self.save()
    
    def is_active(self):
        return self.status == 'OPEN' and timezone.now() <= self.active_until

class Match(models.Model):
    # Badilisha hii - tumia AutoField kwa database ID
    id = models.AutoField(primary_key=True)  # AutoField ita generate automatically
    match_ref = models.CharField(max_length=10)  # Hii ndio itakuwa "M001", "M002"
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='matches')
    teams = models.CharField(max_length=100)
    market = models.CharField(max_length=50)
    selection = models.CharField(max_length=100)
    odds = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        unique_together = ['game', 'match_ref']  # Hakikisha match_ref ni unique kwa game moja tu
    
    def __str__(self):
        return f"{self.match_ref}: {self.teams} - {self.selection}"
    

class Balance(models.Model):
    """
    Model to store account balance
    """
    id = models.AutoField(primary_key=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=10, default='TSh')
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Balance"
        verbose_name_plural = "Balances"
    
    def __str__(self):
        return f"{self.amount} {self.currency}"



class MatchFixture(models.Model):
    """
    Model for match fixtures (different from bet matches)
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