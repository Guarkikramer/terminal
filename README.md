# terminal

# Terminal Avanzada - Gestor de Comandos Inteligente

![Python](https://img.shields.io/badge/python-3.7%2B-blue)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15%2B-green)
![SQLite](https://img.shields.io/badge/SQLite-3-lightgrey)

Una herramienta gráfica para gestionar, ejecutar y organizar comandos de terminal con historial, aliases y capacidades de importación/exportación.

## Características Principales

✅ **Ejecución avanzada de comandos**  
✅ **Gestión de aliases** (crear, editar, eliminar)  
✅ **Historial completo** con favoritos y búsqueda  
✅ **Autocompletado inteligente** de rutas y comandos  
✅ **Exportación/importación** de configuraciones (JSON)  
✅ **Interfaz moderna** con temas personalizables  
✅ **Base de datos SQLite** para almacenamiento persistente  

## Instalación

1. Clona el repositorio:
    ```bash
    git clone https://github.com/tu-usuario/terminal-avanzada.git
    cd terminal-avanzada
    ```
2. Instala las dependencias:
    ```bash
    pip install -r requirements.txt
    ```
3. Ejecuta la aplicación:
    ```bash
    python main.py
    ```

## Uso Básico

### Ejecutar Comandos
1. Escribe tu comando en el campo de entrada.
2. Presiona Enter o haz clic en "Ejecutar".

### Guardar Aliases
1. Ejecuta un comando.
2. Haz clic en "Guardar Alias".
3. Proporciona un nombre y descripción.

### Gestionar Historial
- Marca comandos como favoritos ★.
- Doble clic para re-ejecutar.
- Exporta a archivo de texto.

## Estructura del Proyecto

```plaintext
terminal-avanzada/
├── database/           # Base de datos SQLite
├── main.py             # Aplicación principal
├── requirements.txt    # Dependencias
└── README.md           # Este archivo
Requisitos
Python 3.7+
PyQt5
SQLite3
Instala las dependencias con:

bash
pip install PyQt5
Contribuciones
¡Las contribuciones son bienvenidas! Por favor abre un Issue o Pull Request para:

Reportar bugs
Sugerir mejoras
Añadir nuevas características
Licencia
Este proyecto está bajo la licencia MIT. Consulta el archivo LICENSE para más detalles.

¿Cansado de memorizar comandos? ¡Esta herramienta hace la vida más fácil! 🚀
