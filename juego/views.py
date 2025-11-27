# juego/views.py
import random
from django.shortcuts import render, redirect, get_object_or_404
from .models import GameAttempt, Question

SESSION_ATTEMPT_KEY = "current_attempt_id"

# Lista de premios (pregunta 1..N)
PREMIOS = [100, 200, 300, 500, 1000, 2000, 4000, 8000, 16000, 32000]


def home(request):
    """
    Vista de inicio: formulario con nombre, documento y botón Jugar.
    """
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        document = request.POST.get("document", "").strip()

        if not name or not document:
            return render(request, "juego/home.html", {
                "error": "El nombre y el documento son obligatorios."
            })

        # Crear un nuevo intento de juego
        attempt = GameAttempt.objects.create(
            name=name,
            document=document,
            current_question_number=1,
            max_reached_question=0,
            current_prize=0,
        )
        # Guardar id en la sesión
        request.session[SESSION_ATTEMPT_KEY] = attempt.id
        # Limpiar posibles datos de ayudas previos
        for key in ["current_question_id", "ayuda_publico_data", "ayuda_amigo_letra", "mensaje_info"]:
            request.session.pop(key, None)

        return redirect("jugar")

    return render(request, "juego/home.html")


def get_current_attempt(request):
    """
    Helper para obtener el intento actual desde la sesión.
    """
    attempt_id = request.session.get(SESSION_ATTEMPT_KEY)
    if not attempt_id:
        return None
    return get_object_or_404(GameAttempt, id=attempt_id)


def _build_escalera(attempt):
    """
    Construye la estructura de la escalera de premios:
    nivel, premio, es_actual.
    """
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
    """
    Vista principal del juego: muestra la pregunta actual, estado,
    escalera de premios y resultados de ayudas.
    """
    attempt = get_current_attempt(request)
    if not attempt:
        return redirect("home")

    # Si ya terminó, mostrar resultado
    if attempt.finished:
        return render(request, "juego/resultado.html", {"attempt": attempt})

    # Dificultad actual según la pregunta
    difficulty = attempt.get_current_difficulty()

    # Buscar pregunta aleatoria activa de esa dificultad
    question = Question.objects.filter(
        difficulty=difficulty,
        is_active=True
    ).order_by('?').first()

    if not question:
        # No hay preguntas disponibles → consideramos que ganó con el premio actual
        attempt.finished = True
        attempt.finished_reason = "WIN"
        attempt.save()
        return render(request, "juego/resultado.html", {"attempt": attempt})

    # Premio del nivel actual
    idx = attempt.current_question_number - 1
    premio_nivel = PREMIO_ACTUAL = 0
    if 0 <= idx < len(PREMIOS):
        premio_nivel = PREMIOS[idx]

    # Guardamos id de la pregunta actual en sesión (para validar al responder)
    request.session["current_question_id"] = question.id

    # Resultado de ayudas (si existen en sesión)
    ayuda_publico_data = request.session.pop("ayuda_publico_data", None)
    ayuda_amigo_letra = request.session.pop("ayuda_amigo_letra", None)
    mensaje_info = request.session.pop("mensaje_info", None)

    # Opciones deshabilitadas por 50:50
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
    """
    Procesa la respuesta seleccionada por el usuario.
    """
    if request.method != "POST":
        return redirect("jugar")

    attempt = get_current_attempt(request)
    if not attempt:
        return redirect("home")

    if attempt.finished:
        return render(request, "juego/resultado.html", {"attempt": attempt})

    question_id = request.session.get("current_question_id")
    question = get_object_or_404(Question, id=question_id)

    selected = request.POST.get("option")  # 'A', 'B', 'C' o 'D'

    # Actualizamos hasta qué pregunta llegó (por si pierde)
    if attempt.current_question_number > attempt.max_reached_question:
        attempt.max_reached_question = attempt.current_question_number

    # Limpia las ayudas específicas de la pregunta anterior (50:50 solo aplica a la actual)
    attempt.fifty_disabled_options = None

    if selected == question.correct_option:
        # Respuesta correcta
        idx = attempt.current_question_number - 1
        if 0 <= idx < len(PREMIOS):
            attempt.current_prize = PREMIOS[idx]

        attempt.current_question_number += 1

        # Si supera el número de premios, ganó
        if attempt.current_question_number > len(PREMIOS):
            attempt.finished = True
            attempt.finished_reason = "WIN"

        attempt.save()
        return redirect("jugar")
    else:
        # Respuesta incorrecta → pierde
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
    question = get_object_or_404(Question, id=question_id)

    # 50:50: deshabilitar 2 opciones incorrectas
    correcta = question.correct_option  # 'A'..'D'
    todas = ['A', 'B', 'C', 'D']
    restantes = [o for o in todas if o != correcta]
    deshabilitar = random.sample(restantes, 2)
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
    question = get_object_or_404(Question, id=question_id)

    correcta_map = {
        'A': 0,
        'B': 1,
        'C': 2,
        'D': 3,
    }
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

    # Guardamos en sesión para mostrar en la siguiente carga de 'jugar'
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
    question = get_object_or_404(Question, id=question_id)

    # 80% de probabilidad de acertar
    correcta = question.correct_option  # 'A'..'D'
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

    # Simplemente marcamos que se cambió la pregunta y limpiamos 50:50
    attempt.used_switch = True
    attempt.fifty_disabled_options = None
    attempt.save()

    # Al volver a 'jugar', se generará otra pregunta aleatoria del mismo nivel
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