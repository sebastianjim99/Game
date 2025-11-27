from django.db import migrations

def cargar_preguntas(apps, schema_editor):
    Question = apps.get_model("juego", "Question")

    preguntas = [
        # ============================
        #      PREGUNTAS FÁCILES
        # ============================
        {
            "text": "¿Cuál es el océano más grande del mundo?",
            "option_a": "Atlántico",
            "option_b": "Índico",
            "option_c": "Pacífico",
            "option_d": "Ártico",
            "correct_option": "C",
            "difficulty": "EASY",
        },
        {
            "text": "¿Cuál es el planeta más cercano al Sol?",
            "option_a": "Venus",
            "option_b": "Mercurio",
            "option_c": "Marte",
            "option_d": "Júpiter",
            "correct_option": "B",
            "difficulty": "EASY",
        },
        {
            "text": "¿Cuántos días tiene un año bisiesto?",
            "option_a": "365",
            "option_b": "366",
            "option_c": "364",
            "option_d": "360",
            "correct_option": "B",
            "difficulty": "EASY",
        },
        {
            "text": "¿Qué país es famoso por la Torre Eiffel?",
            "option_a": "Italia",
            "option_b": "Francia",
            "option_c": "España",
            "option_d": "Alemania",
            "correct_option": "B",
            "difficulty": "EASY",
        },
        {
            "text": "¿Cuál es el idioma más hablado en el mundo?",
            "option_a": "Inglés",
            "option_b": "Mandarín",
            "option_c": "Español",
            "option_d": "Árabe",
            "correct_option": "B",
            "difficulty": "EASY",
        },

        # ============================
        #    PREGUNTAS INTERMEDIAS
        # ============================
        {
            "text": "¿Cuál es el metal más abundante en la corteza terrestre?",
            "option_a": "Hierro",
            "option_b": "Aluminio",
            "option_c": "Cobre",
            "option_d": "Plata",
            "correct_option": "B",
            "difficulty": "MEDIUM",
        },
        {
            "text": "¿Quién escribió Cien años de soledad?",
            "option_a": "Julio Cortázar",
            "option_b": "Mario Vargas Llosa",
            "option_c": "Gabriel García Márquez",
            "option_d": "Pablo Neruda",
            "correct_option": "C",
            "difficulty": "MEDIUM",
        },
        {
            "text": "¿En qué año llegó el ser humano a la Luna?",
            "option_a": "1969",
            "option_b": "1971",
            "option_c": "1959",
            "option_d": "1965",
            "correct_option": "A",
            "difficulty": "MEDIUM",
        },
        {
            "text": "¿Cuál es el país más grande del mundo?",
            "option_a": "Canadá",
            "option_b": "Rusia",
            "option_c": "China",
            "option_d": "Estados Unidos",
            "correct_option": "B",
            "difficulty": "MEDIUM",
        },
        {
            "text": "¿Qué vitamina produce el cuerpo humano al exponerse al sol?",
            "option_a": "Vitamina A",
            "option_b": "Vitamina D",
            "option_c": "Vitamina C",
            "option_d": "Vitamina K",
            "correct_option": "B",
            "difficulty": "MEDIUM",
        },

        # ============================
        #      PREGUNTAS DIFÍCILES
        # ============================
        {
            "text": "¿Qué científico propuso la teoría del Big Bang?",
            "option_a": "Edwin Hubble",
            "option_b": "Georges Lemaître",
            "option_c": "Stephen Hawking",
            "option_d": "Max Planck",
            "correct_option": "B",
            "difficulty": "HARD",
        },
        {
            "text": "¿Cuál es el río más largo del mundo según estudios modernos?",
            "option_a": "Amazonas",
            "option_b": "Nilo",
            "option_c": "Yangtsé",
            "option_d": "Misisipi",
            "correct_option": "A",
            "difficulty": "HARD",
        },
        {
            "text": "¿En qué año cayó el Imperio Romano de Occidente?",
            "option_a": "395",
            "option_b": "410",
            "option_c": "476",
            "option_d": "529",
            "correct_option": "C",
            "difficulty": "HARD",
        },
        {
            "text": "¿Cuál es el elemento con mayor punto de fusión?",
            "option_a": "Tungsteno",
            "option_b": "Carbono",
            "option_c": "Osmio",
            "option_d": "Rutenio",
            "correct_option": "A",
            "difficulty": "HARD",
        },
        {
            "text": "¿Qué país tiene más islas en el mundo?",
            "option_a": "Filipinas",
            "option_b": "Noruega",
            "option_c": "Japón",
            "option_d": "Suecia",
            "correct_option": "D",
            "difficulty": "HARD",
        },
    ]

    for p in preguntas:
        Question.objects.get_or_create(
            text=p["text"],
            defaults=p
        )


def revertir_carga(apps, schema_editor):
    Question = apps.get_model("juego", "Question")
    textos = [
        "¿Cuál es el océano más grande del mundo?",
        "¿Cuál es el planeta más cercano al Sol?",
        "¿Cuántos días tiene un año bisiesto?",
        "¿Qué país es famoso por la Torre Eiffel?",
        "¿Cuál es el idioma más hablado en el mundo?",
        "¿Cuál es el metal más abundante en la corteza terrestre?",
        "¿Quién escribió Cien años de soledad?",
        "¿En qué año llegó el ser humano a la Luna?",
        "¿Cuál es el país más grande del mundo?",
        "¿Qué vitamina produce el cuerpo humano al exponerse al sol?",
        "¿Qué científico propuso la teoría del Big Bang?",
        "¿Cuál es el río más largo del mundo según estudios modernos?",
        "¿En qué año cayó el Imperio Romano de Occidente?",
        "¿Cuál es el elemento con mayor punto de fusión?",
        "¿Qué país tiene más islas en el mundo?"
    ]
    Question.objects.filter(text__in=textos).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('juego', '0001_initial'),  # 🔥 AJUSTA si tu número de migración inicial es distinto
    ]

    operations = [
        migrations.RunPython(cargar_preguntas, revertir_carga),
    ]