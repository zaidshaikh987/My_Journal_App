from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Q
from datetime import timedelta, datetime

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    last_journal_date = models.DateField(null=True, blank=True)
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.user.username}'s profile"

    def update_streak(self):
        today = timezone.now().date()
        
        if not self.last_journal_date:
            self.current_streak = 1
        elif self.last_journal_date == today - timedelta(days=1):
            self.current_streak += 1
        elif self.last_journal_date != today:
            self.current_streak = 1
        
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak
            
        self.last_journal_date = today
        self.save()
        return self.current_streak

class JournalEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="entries")
    title = models.CharField(max_length=200, default="Untitled")
    content = models.TextField()
    tags = models.ManyToManyField(Tag, blank=True, related_name="tag_entries")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.title} - {self.date}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Update user's streak when a new entry is created
        if is_new and hasattr(self.user, 'profile'):
            self.user.profile.update_streak()

    def serialize(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "tags": [tag.name for tag in self.tags.all()],
            "created_at": self.created_at.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "updated_at": self.updated_at.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "date": self.date.strftime("%Y-%m-%d")
        }

    class Meta:
        ordering = ["-date"]
        verbose_name_plural = "Journal Entries"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
