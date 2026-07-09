Grimm's World Forge — Estado del Proyecto (Junio 2026)
Objetivo

Grimm's World Forge es una aplicación offline desarrollada en Python + PySide6 para crear, gestionar y simular mundos de ficción.

El objetivo no es solo generar contenido aleatorio, sino construir un simulador narrativo emergente, donde las historias surjan de las acciones y decisiones de las entidades, no de eventos escritos manualmente.

Filosofía del proyecto

Hay tres niveles claramente separados:

1. Generación

Crear entidades.

Ejemplos:

NPC
Ciudad
Reino
Ejército
Criatura
Reliquia
Hechizo
Sistema de magia
Facción
etc.

Toda la generación utiliza oráculos y listas JSON.

2. Persistencia

Todo queda almacenado.

Actualmente existen archivos como:

entities/
    npcs.json
    locations.json
    kingdoms.json
    factions.json
    creatures.json
    armies.json
    relics.json
    items.json
    weapons.json
    armors.json
    foods.json

    world_map.json
    world_events.json
    world_time.json
    relations.json

Cada entidad tiene:

{
    "id":"",
    "name":"",
    "type":"",
    "meta":{},
    "data":{},
    "effects":{}
}
3. Simulación

Aquí vive el mundo.

No genera cosas.

Hace evolucionar lo existente.

Arquitectura actual

Actualmente existen servicios separados.

name_generator_service

Genera nombres.

Actualmente soporta:

Personas
Lugares
Reinos
Armas
Armaduras
Criaturas
Artefactos
Facciones
world_map_service

Guarda posiciones del mapa.

world_simulation_service

Motor principal.

Actualmente hace:

mover NPC
mover criaturas
mover ejércitos
registrar eventos
producir recursos
reacciones básicas
world_time_service

Controla:

turnos
día
mes
año
entity_registry_service

Carga únicamente las entidades necesarias según el widget.

Perfiles actuales:

editor
world
relations
encounters

Esto eliminó los problemas de rendimiento por cargar miles de poderes.

Mapa

El mapa ya posee:

✔ zoom

✔ mover nodos

✔ guardar posiciones

✔ búsqueda

✔ filtro por tipo

✔ agregar/quitar entidades

✔ Registro del Mundo

Registro del Mundo

Cada turno genera eventos persistentes.

Actualmente:

{
    "world_date":"",
    "event_type":"",
    "title":"",
    "description":"",
    "source":{},
    "related":[]
}
Generadores existentes

Actualmente existen widgets para:

NPC

Ubicaciones

Facciones

Reliquias

Ejércitos

Comida

Objetos

Encuentros

Magia

Hechizos

Editor

Mapa

Relaciones

Mundos

etc.

Magia

Existe:

Sistema de magia

Generador modular de hechizos

Biblioteca de hechizos

Spell Components

La magia es independiente de los NPC.

Un NPC puede aprender magia posteriormente.

Filosofía de generación

NO buscamos coherencia absoluta.

La aleatoriedad interesante es bienvenida.

Ejemplo:

Un elfo inventor con látigo.

Eso genera historias.

Objetivo actual

Estamos entrando al simulador.

Queremos dejar atrás eventos puramente narrativos.

Ahora los eventos deben modificar realmente el mundo.

Próxima arquitectura

Se creará:

world_ai_service.py

Será el cerebro del mundo.

No moverá entidades al azar.

Cada entidad tendrá:

{
    "needs":{},
    "goals":[],
    "knowledge":[],
    "personality":{},
    "state":{},
    "party_id":null
}
Las ciudades

Las ciudades dejarán de producir eventos.

Ahora producirán recursos reales.

Ejemplo:

Puerto

comercio

pescado

rumores

viajeros

Universidad

conocimiento

magia

investigación

Fortaleza

soldados

armas

reclutas

Villa

alimentos

madera

ganado

Ruinas

reliquias

magia

peligro

Objetivo final

Crear un verdadero simulador emergente.

No un generador de historias.

Las historias deben surgir porque:

los NPC toman decisiones,

las ciudades producen,

los ejércitos marchan,

las criaturas cazan,

las facciones crecen,

los personajes forman grupos,

aprenden magia,

consiguen objetos,

mueren,

dejan botín,

crean leyendas,

y el Registro del Mundo conserva toda esa historia.

Hay una cosa más que añadiría

Después de tantos meses trabajando juntos, ya veo hacia dónde está evolucionando Grimm's World Forge. Al principio parecía un generador de oráculos, pero ahora está convirtiéndose en un motor de simulación universal.

Eso cambia muchas decisiones de diseño.

Yo incluiría una sección de principios de diseño, porque son reglas que hemos seguido una y otra vez y que un chat nuevo no conocería:

Todo debe ser modular y ampliable por JSON. Si mañana quieres agregar un nuevo tipo de entidad o un nuevo sistema de magia, no debería requerir reescribir el motor.
Los sistemas deben ser agnósticos a la ambientación. Nada debe asumir que el mundo es medieval; el mismo motor debe servir para fantasía, ciencia ficción, cyberpunk o terror.
Las consecuencias deben ser más importantes que los eventos. Un evento solo es valioso si cambia el estado del mundo.
La generación y la simulación son etapas distintas. Primero se crea el mundo, luego el mundo vive.
La narrativa es un resultado, no una entrada. El Registro del Mundo cuenta lo que pasó porque el simulador tomó decisiones.

Con ese documento, el siguiente chat tendría prácticamente toda la filosofía, la arquitectura y el estado del proyecto, y podríamos continuar desarrollando sin tener que reconstruir meses de contexto. De hecho, te recomendaría guardarlo como PROJECT_CONTEXT.md dentro del proyecto; así servirá tanto para futuras conversaciones como para cualquier colaborador que se una al desarrollo.