from django.db import models


class Difficulty(models.TextChoices):
    EASY = 'EASY', 'Fácil'
    MEDIUM = 'MEDIUM', 'Media'
    HARD = 'HARD', 'Difícil'


class Question(models.Model):
    text = models.TextField("Texto de la pregunta")
    option_a = models.CharField("Opción A", max_length=255)
    option_b = models.CharField("Opción B", max_length=255)
    option_c = models.CharField("Opción C", max_length=255)
    option_d = models.CharField("Opción D", max_length=255)

    CORRECT_CHOICES = [
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
    ]
    correct_option = models.CharField(
        "Opción correcta",
        max_length=1,
        choices=CORRECT_CHOICES
    )

    difficulty = models.CharField(
        "Dificultad",
        max_length=10,
        choices=Difficulty.choices,
        default=Difficulty.EASY
    )

    is_active = models.BooleanField("Activa", default=True)

    def __str__(self):
        return f"[{self.get_difficulty_display()}] {self.text[:60]}..."


class GameAttempt(models.Model):
    name = models.CharField("Nombre jugador", max_length=150)
    document = models.CharField("Documento", max_length=50)
    created_at = models.DateTimeField("Fecha de intento", auto_now_add=True)

    current_question_number = models.PositiveIntegerField(default=1)
    max_reached_question = models.PositiveIntegerField(default=0)
    current_prize = models.PositiveIntegerField(default=0)
    used_5050 = models.BooleanField(default=False)
    used_public = models.BooleanField(default=False)
    used_friend = models.BooleanField(default=False)
    used_switch = models.BooleanField(default=False)

    # Guardamos las opciones deshabilitadas por 50:50, ej: "B,D"
    fifty_disabled_options = models.CharField(max_length=10, blank=True, null=True)

    FINISH_REASONS = [
        ('WIN', 'Ganó'),
        ('LOSE', 'Perdió'),
        ('TIME', 'Tiempo agotado'),
        ('QUIT', 'Abandono'),
        (None, 'En juego'),
    ]
    finished_reason = models.CharField(
        "Motivo de finalización",
        max_length=10,
        choices=FINISH_REASONS,
        null=True,
        blank=True
    )
    finished = models.BooleanField(default=False)

    def __str__(self):
        estado = "Terminado" if self.finished else "En juego"
        return f"{self.name} ({self.document}) - {estado} - Pregunta {self.max_reached_question}"

    def get_current_difficulty(self):
        if 1 <= self.current_question_number <= 5:
            return Difficulty.EASY
        elif 6 <= self.current_question_number <= 10:
            return Difficulty.MEDIUM
        else:
            return Difficulty.HARD
        
class AttemptQuestion(models.Model):
    attempt = models.ForeignKey(
        GameAttempt,
        on_delete=models.CASCADE,
        related_name="attempt_questions"
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE
    )
    question_number = models.PositiveIntegerField()  # número de la pregunta en el juego (1,2,3,...)
    asked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('attempt', 'question')  # la misma pregunta no se repite en el mismo intento

    def __str__(self):
        return f"Intento {self.attempt_id} - Pregunta #{self.question_number}: {self.question_id}"