# juego/views.py
import random
from django.shortcuts import render, redirect, get_object_or_404
from .models import GameAttempt, Question, AttemptQuestion

SESSION_ATTEMPT_KEY = "current_attempt_id"
PREMIOS = [100, 200, 300, 500, 1000, 2000, 4000, 8000, 16000, 32000, 64000, 125000, 250000, 500000, 1000000 ]


def home(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        document = request.POST.get("document", "").strip()

        if not name or not document:
            return render(request, "juego/home.html", {
                "error": "El nombre y el documento son obligatorios."
            })

        attempt = GameAttempt.objects.create(
            name=name,
            document=document,
            current_question_number=1,
            max_reached_question=0,
            current_prize=0,
        )
        request.session[SESSION_ATTEMPT_KEY] = attempt.id

        # limpiamos cualquier rastro de pregunta/ayudas previas
        for key in ["current_question_id", "ayuda_publico_data",
                    "ayuda_amigo_letra", "mensaje_info"]:
            request.session.pop(key, None)

        return redirect("jugar")

    return render(request, "juego/home.html")


def get_current_attempt(request):
    attempt_id = request.session.get(SESSION_ATTEMPT_KEY)
    if not attempt_id:
        return None
    return get_object_or_404(GameAttempt, id=attempt_id)


def _build_escalera(attempt):
    escalera = []
    total = len(PREMIOS)
    nivel_actual_index = attempt.current_question_number - 1  # 0-based

    for i, premio in enumerate(reversed(PREMIOS)):
        nivel_real = total - 1 - i  # índice real 0-based
        escalera.append({
            "numero": nivel_real + 1,
            "premio": premio,
            "es_actual": (nivel_real == nivel_actual_index),
        })
    return escalera


def jugar(request):
    attempt = get_current_attempt(request)
    if not attempt:
        return redirect("home")

    if attempt.finished:
        return render(request, "juego/resultado.html", {"attempt": attempt})

    # 1) Intentamos reutilizar la pregunta actual de la sesión
    current_q_id = request.session.get("current_question_id")
    question = None
    if current_q_id:
        question = Question.objects.filter(
            id=current_q_id,
            is_active=True
        ).first()

    # 2) Si no hay pregunta en sesión o la pregunta ya no existe, escogemos una nueva
    if question is None:
        difficulty = attempt.get_current_difficulty()

        # IDs de preguntas que ya se mostraron en este intento
        used_ids = AttemptQuestion.objects.filter(
            attempt=attempt
        ).values_list('question_id', flat=True)

        # Preguntas activas de la dificultad actual que NO se han usado
        qs = Question.objects.filter(
            difficulty=difficulty,
            is_active=True
        ).exclude(id__in=used_ids)

        question = qs.order_by('?').first()

        if not question:
            # No quedan más preguntas disponibles para esta dificultad
            attempt.finished = True
            attempt.finished_reason = "WIN"
            attempt.save()
            return render(request, "juego/resultado.html", {"attempt": attempt})

        # Guardar en sesión la nueva pregunta
        request.session["current_question_id"] = question.id

        # Registrar que esta pregunta se mostró en este intento
        AttemptQuestion.objects.get_or_create(
            attempt=attempt,
            question=question,
            defaults={"question_number": attempt.current_question_number}
        )

        # Reset de 50:50
        attempt.fifty_disabled_options = None
        attempt.save()

    idx = attempt.current_question_number - 1
    premio_nivel = 0
    if 0 <= idx < len(PREMIOS):
        premio_nivel = PREMIOS[idx]

    ayuda_publico_data = request.session.pop("ayuda_publico_data", None)
    ayuda_amigo_letra = request.session.pop("ayuda_amigo_letra", None)
    mensaje_info = request.session.pop("mensaje_info", None)

    disabled_letters = []
    if attempt.fifty_disabled_options:
        disabled_letters = [l for l in attempt.fifty_disabled_options.split(",") if l]

    contexto = {
        "attempt": attempt,
        "question": question,
        "premio_nivel": premio_nivel,
        "total_preguntas": len(PREMIOS),
        "escalera": _build_escalera(attempt),
        "ayuda_publico_data": ayuda_publico_data,
        "ayuda_amigo_letra": ayuda_amigo_letra,
        "mensaje_info": mensaje_info,
        "disabled_letters": disabled_letters,
    }
    return render(request, "juego/jugar.html", contexto)


def responder(request):
    if request.method != "POST":
        return redirect("jugar")

    attempt = get_current_attempt(request)
    if not attempt:
        return redirect("home")

    if attempt.finished:
        return render(request, "juego/resultado.html", {"attempt": attempt})

    question_id = request.session.get("current_question_id")
    question = get_object_or_404(Question, id=question_id)

    selected = request.POST.get("option")  # 'A', 'B', 'C', 'D'

    if attempt.current_question_number > attempt.max_reached_question:
        attempt.max_reached_question = attempt.current_question_number

    # Esta pregunta ya no se usará más; borramos el ID para que en la siguiente
    # se seleccione una nueva.
    request.session.pop("current_question_id", None)
    attempt.fifty_disabled_options = None

    if selected == question.correct_option:
        idx = attempt.current_question_number - 1
        if 0 <= idx < len(PREMIOS):
            attempt.current_prize = PREMIOS[idx]

        attempt.current_question_number += 1

        if attempt.current_question_number > len(PREMIOS):
            attempt.finished = True
            attempt.finished_reason = "WIN"

        attempt.save()
        return redirect("jugar")
    else:
        attempt.finished = True
        attempt.finished_reason = "LOSE"
        attempt.save()
        return render(request, "juego/resultado.html", {"attempt": attempt})


# ======================
#        AYUDAS
# ======================

def ayuda_5050(request):
    attempt = get_current_attempt(request)
    if not attempt:
        return redirect("home")
    if attempt.finished:
        return redirect("jugar")

    if attempt.used_5050:
        request.session["mensaje_info"] = "Ya utilizaste la ayuda 50:50."
        return redirect("jugar")

    question_id = request.session.get("current_question_id")
    if not question_id:
        request.session["mensaje_info"] = "No hay pregunta activa para aplicar 50:50."
        return redirect("jugar")

    question = get_object_or_404(Question, id=question_id)

    correcta = question.correct_option  # 'A'..'D'
    todas = ['A', 'B', 'C', 'D']
    restantes = [o for o in todas if o != correcta]
    deshabilitar = random.sample(restantes, 2)  # SIEMPRE SOLO INCORRECTAS
    attempt.fifty_disabled_options = ",".join(deshabilitar)
    attempt.used_5050 = True
    attempt.save()

    return redirect("jugar")


def ayuda_publico(request):
    attempt = get_current_attempt(request)
    if not attempt:
        return redirect("home")
    if attempt.finished:
        return redirect("jugar")

    if attempt.used_public:
        request.session["mensaje_info"] = "Ya usaste la ayuda 'Preguntar al público'."
        return redirect("jugar")

    question_id = request.session.get("current_question_id")
    if not question_id:
        request.session["mensaje_info"] = "No hay pregunta activa para preguntar al público."
        return redirect("jugar")

    question = get_object_or_404(Question, id=question_id)

    correcta_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
    idx_correcta = correcta_map[question.correct_option]

    porcentajes = [0, 0, 0, 0]
    base_correcta = random.randint(40, 70)
    restante = 100 - base_correcta
    indices = [0, 1, 2, 3]
    indices.remove(idx_correcta)

    for i in indices[:-1]:
        val = random.randint(0, restante)
        porcentajes[i] = val
        restante -= val
    porcentajes[indices[-1]] = restante
    porcentajes[idx_correcta] = base_correcta

    request.session["ayuda_publico_data"] = porcentajes
    attempt.used_public = True
    attempt.save()

    return redirect("jugar")


def ayuda_amigo(request):
    attempt = get_current_attempt(request)
    if not attempt:
        return redirect("home")
    if attempt.finished:
        return redirect("jugar")

    if attempt.used_friend:
        request.session["mensaje_info"] = "Ya usaste la ayuda 'Llamar a un amigo'."
        return redirect("jugar")

    question_id = request.session.get("current_question_id")
    if not question_id:
        request.session["mensaje_info"] = "No hay pregunta activa para llamar al amigo."
        return redirect("jugar")

    question = get_object_or_404(Question, id=question_id)

    # Si quieres que SIEMPRE acierte, pon directamente:
    # sugerida = question.correct_option
    # Si quieres mantener probabilidad de error, deja esto:
    correcta = question.correct_option
    opciones = ['A', 'B', 'C', 'D']
    if random.random() < 0.8:
        sugerida = correcta
    else:
        restantes = [o for o in opciones if o != correcta]
        sugerida = random.choice(restantes)

    request.session["ayuda_amigo_letra"] = sugerida
    attempt.used_friend = True
    attempt.save()

    return redirect("jugar")


def ayuda_cambiar(request):
    attempt = get_current_attempt(request)
    if not attempt:
        return redirect("home")
    if attempt.finished:
        return redirect("jugar")

    if attempt.used_switch:
        request.session["mensaje_info"] = "Ya usaste la ayuda 'Cambiar de pregunta'."
        return redirect("jugar")

    current_q_id = request.session.get("current_question_id")
    difficulty = attempt.get_current_difficulty()

    # IDs de preguntas ya usadas en este intento
    used_ids = list(
        AttemptQuestion.objects.filter(attempt=attempt).values_list('question_id', flat=True)
    )
    # También evitamos repetir la actual explícitamente
    if current_q_id:
        used_ids.append(current_q_id)

    # Buscar una nueva pregunta NO usada
    qs = Question.objects.filter(
        difficulty=difficulty,
        is_active=True
    ).exclude(id__in=used_ids)

    nueva = qs.order_by('?').first()
    if not nueva:
        request.session["mensaje_info"] = "No hay más preguntas disponibles para cambiar en esta dificultad."
        return redirect("jugar")

    # Cambiamos de pregunta
    request.session["current_question_id"] = nueva.id
    attempt.used_switch = True
    attempt.fifty_disabled_options = None
    attempt.save()

    # Registrar la nueva pregunta como usada en este intento
    AttemptQuestion.objects.get_or_create(
        attempt=attempt,
        question=nueva,
        defaults={"question_number": attempt.current_question_number}
    )

    return redirect("jugar")

def ranking(request):
    """
    Ranking tipo podio:
    - Top 3 en formato podio.
    - Resto de jugadores en tabla.
    Ordenado por:
      1) pregunta máxima alcanzada (desc)
      2) premio actual (desc)
      3) fecha de creación (asc)
    Solo considera juegos finalizados.
    """
    attempts = GameAttempt.objects.filter(finished=True).order_by(
        "-max_reached_question",
        "-current_prize",
        "created_at"
    )

    top3 = list(attempts[:3])
    others = attempts[3:]

    context = {
        "top3": top3,
        "others": others,
    }
    return render(request, "juego/ranking.html", context)
