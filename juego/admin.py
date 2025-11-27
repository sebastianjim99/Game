from django.contrib import admin
from .models import Question, GameAttempt


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("text_short", "difficulty", "is_active")
    list_filter = ("difficulty", "is_active")
    search_fields = ("text",)

    def text_short(self, obj):
        return obj.text[:60]
    text_short.short_description = "Pregunta"


@admin.register(GameAttempt)
class GameAttemptAdmin(admin.ModelAdmin):
    list_display = ("name", "document", "created_at", "max_reached_question", "current_prize", "finished_reason")
    list_filter = ("finished", "finished_reason", "created_at")
    search_fields = ("name", "document")