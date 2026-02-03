import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import re
from groq import Groq
from sympy import symbols, Eq, integrate, diff, simplify, exp, log, sin, cos, sqrt, tan, latex

# --- 1. CONFIGURACIÓN DE LA API ---
#client_groq = Groq(api_key="your groq api here")

# --- 2. BASE DE DATOS DE EJERCICIOS AMPLIADA ---
DB_EJERCICIOS = {
    "Nivel 1: Polinomios Básicos": [
        {"desc": "(2x + y)dx + (x + 2y)dy = 0", "M": "2*x + y", "N": "x + 2*y"},
        {"desc": "(y² - 1)dx + (2xy)dy = 0", "M": "y**2 - 1", "N": "2*x*y"},
        {"desc": "(3x² + y)dx + (x + 3y²)dy = 0", "M": "3*x**2 + y", "N": "x + 3*y**2"},
        {"desc": "(x + y)dx + (x - y)dy = 0", "M": "x + y", "N": "x - y"},
        {"desc": "(2xy + 1)dx + (x² + 1)dy = 0", "M": "2*x*y + 1", "N": "x**2 + 1"},
    ],
    "Nivel 2: Funciones Trigonométricas": [
        {"desc": "(eˣ + y)dx + (x + sin(y))dy = 0", "M": "exp(x) + y", "N": "x + sin(y)"},
        {"desc": "(cos(x) + y)dx + (x + sin(y))dy = 0", "M": "cos(x) + y", "N": "x + sin(y)"},
        {"desc": "(y·cos(x) + 1)dx + sin(x)dy = 0", "M": "y*cos(x) + 1", "N": "sin(x)"},
        {"desc": "(sin(x)·cos(y))dx + (cos(x)·sin(y))dy = 0", "M": "sin(x)*cos(y)", "N": "cos(x)*sin(y)"},
    ],
    "Nivel 3: Funciones Exponenciales y Logarítmicas": [
        {"desc": "(eˣ + y)dx + (x + eʸ)dy = 0", "M": "exp(x) + y", "N": "x + exp(y)"},
        {"desc": "(ln(y))dx + (x/y + y)dy = 0", "M": "log(y)", "N": "x/y + y"},
        {"desc": "(yeˣʸ + 2x)dx + (xeˣʸ + 2y)dy = 0", "M": "y*exp(x*y) + 2*x", "N": "x*exp(x*y) + 2*y"},
        {"desc": "(eˣ·cos(y))dx - (eˣ·sin(y))dy = 0", "M": "exp(x)*cos(y)", "N": "-exp(x)*sin(y)"},
    ],
    "Nivel 4: Ecuaciones No Exactas (Requieren μ)": [
        {"desc": "(y)dx + (x·y - x)dy = 0", "M": "y", "N": "x*y - x"},
        {"desc": "(x² + y² + x)dx + (xy)dy = 0", "M": "x**2 + y**2 + x", "N": "x*y"},
        {"desc": "(y)dx + (2x - yeʸ)dy = 0", "M": "y", "N": "2*x - y*exp(y)"},
        {"desc": "(3xy + y²)dx + (x² + xy)dy = 0", "M": "3*x*y + y**2", "N": "x**2 + x*y"},
    ],
    "Nivel 5: Mixtas Avanzadas": [
        {"desc": "(x² + y²)dx + (2xy)dy = 0", "M": "x**2 + y**2", "N": "2*x*y"},
        {"desc": "(yeˣ + 2x)dx + (eˣ + 2y)dy = 0", "M": "y*exp(x) + 2*x", "N": "exp(x) + 2*y"},
        {"desc": "(2x·ln(y) + y)dx + (x²/y + x)dy = 0", "M": "2*x*log(y) + y", "N": "x**2/y + x"},
        {"desc": "(cos(x)·eʸ)dx + (sin(x)·eʸ + 1)dy = 0", "M": "cos(x)*exp(y)", "N": "sin(x)*exp(y) + 1"},
    ],
    "Nivel 6: Desafíos Especiales": [
        {"desc": "(x³ + 3xy²)dx + (y³ + 3x²y)dy = 0", "M": "x**3 + 3*x*y**2", "N": "y**3 + 3*x**2*y"},
        {"desc": "(2xy² + x)dx + (2x²y + y)dy = 0", "M": "2*x*y**2 + x", "N": "2*x**2*y + y"},
        {"desc": "(eˣ·sin(y) + eʸ)dx + (eˣ·cos(y) + xeʸ)dy = 0", "M": "exp(x)*sin(y) + exp(y)", "N": "exp(x)*cos(y) + x*exp(y)"},
    ]
}

# --- 3. COLORES Y ESTILOS MODERNOS ---
COLORS = {
    'bg_primary': '#0f172a',
    'bg_secondary': '#1e293b',
    'bg_card': '#334155',
    'accent_blue': '#3b82f6',
    'accent_purple': '#8b5cf6',
    'accent_cyan': '#06b6d4',
    'text_primary': '#f1f5f9',
    'text_secondary': '#94a3b8',
    'success': '#10b981',
    'warning': '#f59e0b',
    'error': '#ef4444',
    'hover': '#475569'
}

# --- 4. LÓGICA MATEMÁTICA Y PRE-PROCESAMIENTO ---
def pre_procesar_entrada(texto):
    """Convierte entrada humana a formato SymPy."""
    potencias = {'²': '**2', '³': '**3', '⁴': '**4', '^': '**'}
    for char, rep in potencias.items():
        texto = texto.replace(char, rep)
    texto = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', texto)
    texto = re.sub(r'([xy])([xy])', r'\1*\2', texto)
    return texto

def a_claro(expr):
    """Formato legible para el usuario."""
    return str(expr).replace('**', '^').replace('*', '·').replace('exp', 'e^').replace('log', 'ln').replace('sqrt', '√')

def obtener_datos_completos_detallado(M_str, N_str):
    """Motor central mejorado con explicaciones paso a paso."""
    x, y = symbols('x y')
    M_original, N_original = simplify(M_str), simplify(N_str)
    M, N = M_original, N_original
    My, Nx = diff(M, y), diff(N, x)
    diff_c = simplify(My - Nx)
    
    datos = {"M": M, "N": N, "My": My, "Nx": Nx, "es_exacta": diff_c == 0}
    
    # Crear explicación detallada
    pasos = "═" * 70 + "\n"
    pasos += "  SOLUCIÓN DETALLADA PASO A PASO\n"
    pasos += "═" * 70 + "\n\n"
    
    # PASO 1: Identificación
    pasos += "┌─ PASO 1: IDENTIFICACIÓN DE LA ECUACIÓN ─────────────────────────┐\n"
    pasos += "│\n"
    pasos += f"│  Ecuación dada: M(x,y)dx + N(x,y)dy = 0\n"
    pasos += f"│\n"
    pasos += f"│  Donde:\n"
    pasos += f"│    M(x,y) = {a_claro(M)}\n"
    pasos += f"│    N(x,y) = {a_claro(N)}\n"
    pasos += "│\n"
    pasos += "└──────────────────────────────────────────────────────────────────┘\n\n"
    
    # PASO 2: Cálculo de derivadas parciales
    pasos += "┌─ PASO 2: VERIFICACIÓN DEL CRITERIO DE EXACTITUD ────────────────┐\n"
    pasos += "│\n"
    pasos += "│  Para que una ecuación sea EXACTA debe cumplirse:\n"
    pasos += "│    ∂M/∂y = ∂N/∂x\n"
    pasos += "│\n"
    pasos += "│  Calculamos las derivadas parciales:\n"
    pasos += "│\n"
    pasos += f"│  ∂M/∂y = ∂({a_claro(M)})/∂y\n"
    pasos += f"│         = {a_claro(My)}\n"
    pasos += "│\n"
    pasos += f"│  ∂N/∂x = ∂({a_claro(N)})/∂x\n"
    pasos += f"│         = {a_claro(Nx)}\n"
    pasos += "│\n"
    
    if diff_c == 0:
        pasos += "│  ✓ RESULTADO: ∂M/∂y = ∂N/∂x\n"
        pasos += "│  ✓ La ecuación ES EXACTA\n"
        pasos += "│\n"
        pasos += "└──────────────────────────────────────────────────────────────────┘\n\n"
        
        # PASO 3: Integración de M
        pasos += "┌─ PASO 3: ENCONTRAR LA FUNCIÓN POTENCIAL Ψ(x,y) ─────────────────┐\n"
        pasos += "│\n"
        pasos += "│  Como la ecuación es exacta, existe Ψ(x,y) tal que:\n"
        pasos += "│    ∂Ψ/∂x = M  y  ∂Ψ/∂y = N\n"
        pasos += "│\n"
        pasos += "│  Integramos M respecto a x:\n"
        pasos += "│\n"
        psi = integrate(M, x)
        pasos += f"│  Ψ(x,y) = ∫ M dx = ∫ ({a_claro(M)}) dx\n"
        pasos += f"│         = {a_claro(psi)} + h(y)\n"
        pasos += "│\n"
        pasos += "│  donde h(y) es una función arbitraria de y solamente.\n"
        pasos += "│\n"
        pasos += "└──────────────────────────────────────────────────────────────────┘\n\n"
        
        # PASO 4: Determinar h(y)
        pasos += "┌─ PASO 4: DETERMINAR h(y) ────────────────────────────────────────┐\n"
        pasos += "│\n"
        pasos += "│  Derivamos Ψ(x,y) respecto a y:\n"
        pasos += "│\n"
        psi_y = diff(psi, y)
        pasos += f"│  ∂Ψ/∂y = ∂({a_claro(psi)})/∂y + h'(y)\n"
        pasos += f"│         = {a_claro(psi_y)} + h'(y)\n"
        pasos += "│\n"
        pasos += "│  Igualamos a N(x,y):\n"
        pasos += "│\n"
        h_prim = simplify(N - psi_y)
        pasos += f"│  {a_claro(psi_y)} + h'(y) = {a_claro(N)}\n"
        pasos += f"│  h'(y) = {a_claro(N)} - {a_claro(psi_y)}\n"
        pasos += f"│  h'(y) = {a_claro(h_prim)}\n"
        pasos += "│\n"
        pasos += "│  Integramos h'(y) para obtener h(y):\n"
        pasos += "│\n"
        h = integrate(h_prim, y)
        pasos += f"│  h(y) = ∫ ({a_claro(h_prim)}) dy\n"
        pasos += f"│       = {a_claro(h)}\n"
        pasos += "│\n"
        pasos += "└──────────────────────────────────────────────────────────────────┘\n\n"
        
        # PASO 5: Solución final
        solucion = Eq(psi + h, symbols('C'))
        datos["resultado"] = solucion
        
        pasos += "┌─ PASO 5: SOLUCIÓN GENERAL ───────────────────────────────────────┐\n"
        pasos += "│\n"
        pasos += "│  La función potencial completa es:\n"
        pasos += "│\n"
        pasos += f"│  Ψ(x,y) = {a_claro(psi)} + {a_claro(h)}\n"
        pasos += "│\n"
        pasos += "│  La solución de la ecuación diferencial es:\n"
        pasos += "│\n"
        pasos += f"│  ╔═══════════════════════════════════════════════╗\n"
        pasos += f"│  ║  {a_claro(solucion):^45s}  ║\n"
        pasos += f"│  ╚═══════════════════════════════════════════════╝\n"
        pasos += "│\n"
        pasos += "│  donde C es una constante arbitraria.\n"
        pasos += "│\n"
        pasos += "└──────────────────────────────────────────────────────────────────┘\n"
        
    else:
        # Ecuación NO exacta
        pasos += f"│  ✗ RESULTADO: ∂M/∂y - ∂N/∂x = {a_claro(diff_c)} ≠ 0\n"
        pasos += "│  ✗ La ecuación NO es exacta\n"
        pasos += "│\n"
        pasos += "└──────────────────────────────────────────────────────────────────┘\n\n"
        
        # PASO 3: Buscar factor integrante
        pasos += "┌─ PASO 3: BÚSQUEDA DEL FACTOR INTEGRANTE ─────────────────────────┐\n"
        pasos += "│\n"
        pasos += "│  Para convertir la ecuación en exacta, buscamos un factor\n"
        pasos += "│  integrante μ que dependa solo de x o solo de y.\n"
        pasos += "│\n"
        
        mu_encontrado = False
        
        # Intentar μ(x)
        pasos += "│  OPCIÓN 1: Probamos con μ(x)\n"
        pasos += "│  ─────────────────────────────\n"
        pasos += "│\n"
        pasos += "│  Calculamos: (∂M/∂y - ∂N/∂x) / N\n"
        
        try:
            fx = simplify(diff_c / N)
            pasos += f"│             = ({a_claro(diff_c)}) / ({a_claro(N)})\n"
            pasos += f"│             = {a_claro(fx)}\n"
            pasos += "│\n"
            
            if not fx.has(y):
                pasos += "│  ✓ Esta expresión NO depende de y\n"
                pasos += "│  ✓ Podemos encontrar μ(x) = e^(∫ f(x) dx)\n"
                pasos += "│\n"
                
                try:
                    integral_fx = integrate(fx, x)
                    mu = exp(integral_fx)
                    mu = simplify(mu)
                    
                    pasos += f"│  ∫ f(x) dx = ∫ ({a_claro(fx)}) dx\n"
                    pasos += f"│            = {a_claro(integral_fx)}\n"
                    pasos += "│\n"
                    pasos += f"│  μ(x) = e^({a_claro(integral_fx)})\n"
                    pasos += f"│       = {a_claro(mu)}\n"
                    pasos += "│\n"
                    
                    datos["mu"] = mu
                    datos["tipo_mu"] = "μ(x)"
                    mu_encontrado = True
                    
                    # Multiplicar por μ
                    M = simplify(mu * M_original)
                    N = simplify(mu * N_original)
                    
                    pasos += "└──────────────────────────────────────────────────────────────────┘\n\n"
                    
                    pasos += "┌─ PASO 4: ECUACIÓN EXACTA RESULTANTE ─────────────────────────────┐\n"
                    pasos += "│\n"
                    pasos += "│  Multiplicamos la ecuación original por μ(x):\n"
                    pasos += "│\n"
                    pasos += f"│  M'(x,y) = μ(x) · M(x,y)\n"
                    pasos += f"│          = ({a_claro(mu)}) · ({a_claro(M_original)})\n"
                    pasos += f"│          = {a_claro(M)}\n"
                    pasos += "│\n"
                    pasos += f"│  N'(x,y) = μ(x) · N(x,y)\n"
                    pasos += f"│          = ({a_claro(mu)}) · ({a_claro(N_original)})\n"
                    pasos += f"│          = {a_claro(N)}\n"
                    pasos += "│\n"
                    
                    # Verificar que ahora es exacta
                    My_nueva = diff(M, y)
                    Nx_nueva = diff(N, x)
                    pasos += "│  Verificamos:\n"
                    pasos += f"│  ∂M'/∂y = {a_claro(My_nueva)}\n"
                    pasos += f"│  ∂N'/∂x = {a_claro(Nx_nueva)}\n"
                    pasos += "│  ✓ Ahora la ecuación ES EXACTA\n"
                    pasos += "│\n"
                    pasos += "└──────────────────────────────────────────────────────────────────┘\n\n"
                    
                except:
                    pasos += "│  ✗ No se pudo integrar f(x)\n"
                    pasos += "│\n"
            else:
                pasos += "│  ✗ Esta expresión SÍ depende de y\n"
                pasos += "│  ✗ No podemos usar μ(x)\n"
                pasos += "│\n"
        except:
            pasos += "│  ✗ Error al calcular (∂M/∂y - ∂N/∂x) / N\n"
            pasos += "│\n"
        
        # Si no funcionó μ(x), intentar μ(y)
        if not mu_encontrado:
            pasos += "│  OPCIÓN 2: Probamos con μ(y)\n"
            pasos += "│  ─────────────────────────────\n"
            pasos += "│\n"
            pasos += "│  Calculamos: (∂N/∂x - ∂M/∂y) / M\n"
            
            try:
                gy = simplify(-diff_c / M)
                pasos += f"│             = ({a_claro(-diff_c)}) / ({a_claro(M)})\n"
                pasos += f"│             = {a_claro(gy)}\n"
                pasos += "│\n"
                
                if not gy.has(x):
                    pasos += "│  ✓ Esta expresión NO depende de x\n"
                    pasos += "│  ✓ Podemos encontrar μ(y) = e^(∫ g(y) dy)\n"
                    pasos += "│\n"
                    
                    try:
                        integral_gy = integrate(gy, y)
                        mu = exp(integral_gy)
                        mu = simplify(mu)
                        
                        pasos += f"│  ∫ g(y) dy = ∫ ({a_claro(gy)}) dy\n"
                        pasos += f"│            = {a_claro(integral_gy)}\n"
                        pasos += "│\n"
                        pasos += f"│  μ(y) = e^({a_claro(integral_gy)})\n"
                        pasos += f"│       = {a_claro(mu)}\n"
                        pasos += "│\n"
                        
                        datos["mu"] = mu
                        datos["tipo_mu"] = "μ(y)"
                        mu_encontrado = True
                        
                        # Multiplicar por μ
                        M = simplify(mu * M_original)
                        N = simplify(mu * N_original)
                        
                        pasos += "└──────────────────────────────────────────────────────────────────┘\n\n"
                        
                        pasos += "┌─ PASO 4: ECUACIÓN EXACTA RESULTANTE ─────────────────────────────┐\n"
                        pasos += "│\n"
                        pasos += "│  Multiplicamos la ecuación original por μ(y):\n"
                        pasos += "│\n"
                        pasos += f"│  M'(x,y) = μ(y) · M(x,y)\n"
                        pasos += f"│          = ({a_claro(mu)}) · ({a_claro(M_original)})\n"
                        pasos += f"│          = {a_claro(M)}\n"
                        pasos += "│\n"
                        pasos += f"│  N'(x,y) = μ(y) · N(x,y)\n"
                        pasos += f"│          = ({a_claro(mu)}) · ({a_claro(N_original)})\n"
                        pasos += f"│          = {a_claro(N)}\n"
                        pasos += "│\n"
                        
                        # Verificar
                        My_nueva = diff(M, y)
                        Nx_nueva = diff(N, x)
                        pasos += "│  Verificamos:\n"
                        pasos += f"│  ∂M'/∂y = {a_claro(My_nueva)}\n"
                        pasos += f"│  ∂N'/∂x = {a_claro(Nx_nueva)}\n"
                        pasos += "│  ✓ Ahora la ecuación ES EXACTA\n"
                        pasos += "│\n"
                        pasos += "└──────────────────────────────────────────────────────────────────┘\n\n"
                        
                    except:
                        pasos += "│  ✗ No se pudo integrar g(y)\n"
                        pasos += "│\n"
                else:
                    pasos += "│  ✗ Esta expresión SÍ depende de x\n"
                    pasos += "│  ✗ No podemos usar μ(y)\n"
                    pasos += "│\n"
            except:
                pasos += "│  ✗ Error al calcular (∂N/∂x - ∂M/∂y) / M\n"
                pasos += "│\n"
        
        if not mu_encontrado:
            pasos += "│  ✗ No se encontró factor integrante simple en x o y\n"
            pasos += "│  ✗ Se requieren métodos más avanzados\n"
            pasos += "│\n"
            pasos += "└──────────────────────────────────────────────────────────────────┘\n"
            pasos += "\n" + "═" * 70 + "\n"
            datos["resultado"] = "No se pudo resolver con factores integrantes simples"
            return datos, pasos
    
    # Resolver la ecuación exacta (ya sea original o con μ)
    paso_inicial = 5 if not datos.get("es_exacta", False) else 3
    
    pasos += f"┌─ PASO {paso_inicial}: ENCONTRAR LA FUNCIÓN POTENCIAL Ψ(x,y) ─────────────────┐\n"
    pasos += "│\n"
    pasos += "│  Como la ecuación es exacta, existe Ψ(x,y) tal que:\n"
    pasos += "│    ∂Ψ/∂x = M  y  ∂Ψ/∂y = N\n"
    pasos += "│\n"
    pasos += "│  Integramos M respecto a x:\n"
    pasos += "│\n"
    
    try:
        psi = integrate(M, x)
        pasos += f"│  Ψ(x,y) = ∫ M dx = ∫ ({a_claro(M)}) dx\n"
        pasos += f"│         = {a_claro(psi)} + h(y)\n"
        pasos += "│\n"
        pasos += "│  donde h(y) es una función arbitraria de y solamente.\n"
        pasos += "│\n"
        pasos += "└──────────────────────────────────────────────────────────────────┘\n\n"
        
        # PASO siguiente: Determinar h(y)
        pasos += f"┌─ PASO {paso_inicial + 1}: DETERMINAR h(y) ────────────────────────────────────┐\n"
        pasos += "│\n"
        pasos += "│  Derivamos Ψ(x,y) respecto a y:\n"
        pasos += "│\n"
        psi_y = diff(psi, y)
        pasos += f"│  ∂Ψ/∂y = ∂({a_claro(psi)})/∂y + h'(y)\n"
        pasos += f"│         = {a_claro(psi_y)} + h'(y)\n"
        pasos += "│\n"
        pasos += "│  Igualamos a N(x,y):\n"
        pasos += "│\n"
        h_prim = simplify(N - psi_y)
        pasos += f"│  {a_claro(psi_y)} + h'(y) = {a_claro(N)}\n"
        pasos += f"│  h'(y) = {a_claro(N)} - ({a_claro(psi_y)})\n"
        pasos += f"│  h'(y) = {a_claro(h_prim)}\n"
        pasos += "│\n"
        pasos += "│  Integramos h'(y) para obtener h(y):\n"
        pasos += "│\n"
        h = integrate(h_prim, y)
        pasos += f"│  h(y) = ∫ ({a_claro(h_prim)}) dy\n"
        pasos += f"│       = {a_claro(h)}\n"
        pasos += "│\n"
        pasos += "└──────────────────────────────────────────────────────────────────┘\n\n"
        
        # PASO final: Solución
        solucion = Eq(psi + h, symbols('C'))
        datos["resultado"] = solucion
        
        pasos += f"┌─ PASO {paso_inicial + 2}: SOLUCIÓN GENERAL ───────────────────────────────────┐\n"
        pasos += "│\n"
        pasos += "│  La función potencial completa es:\n"
        pasos += "│\n"
        pasos += f"│  Ψ(x,y) = {a_claro(psi)} + {a_claro(h)}\n"
        pasos += "│\n"
        pasos += "│  La solución de la ecuación diferencial es:\n"
        pasos += "│\n"
        pasos += f"│  ╔═══════════════════════════════════════════════╗\n"
        pasos += f"│  ║  {a_claro(solucion):^45s}  ║\n"
        pasos += f"│  ╚═══════════════════════════════════════════════╝\n"
        pasos += "│\n"
        pasos += "│  donde C es una constante arbitraria.\n"
        pasos += "│\n"
        pasos += "└──────────────────────────────────────────────────────────────────┘\n"
        
    except Exception as e:
        pasos += f"│  ✗ Error al resolver: {str(e)}\n"
        pasos += "│\n"
        pasos += "└──────────────────────────────────────────────────────────────────┘\n"
        datos["resultado"] = f"Error en la resolución: {str(e)}"
    
    pasos += "\n" + "═" * 70 + "\n"
    
    return datos, pasos

# --- 5. WIDGETS PERSONALIZADOS ---
class ModernButton(tk.Canvas):
    def __init__(self, parent, text, command, width=120, height=40, **kwargs):
        super().__init__(parent, width=width, height=height, highlightthickness=0, 
                        bg=COLORS['bg_secondary'], cursor='hand2')
        
        self.command = command
        self.text = text
        self.default_color = kwargs.get('bg', COLORS['accent_blue'])
        self.hover_color = kwargs.get('hover_bg', COLORS['accent_purple'])
        
        self.rect = self.create_rounded_rect(2, 2, width-2, height-2, radius=10, 
                                             fill=self.default_color, outline='')
        
        self.text_id = self.create_text(width//2, height//2, text=text, 
                                       fill=COLORS['text_primary'], 
                                       font=('Segoe UI', 10, 'bold'))
        
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
        self.bind('<Button-1>', lambda e: command())
    
    def create_rounded_rect(self, x1, y1, x2, y2, radius=25, **kwargs):
        points = [x1+radius, y1,
                 x1+radius, y1, x2-radius, y1,
                 x2-radius, y1, x2, y1,
                 x2, y1+radius, x2, y1+radius,
                 x2, y1+radius, x2, y2-radius,
                 x2, y2-radius, x2, y2,
                 x2-radius, y2, x2-radius, y2,
                 x2-radius, y2, x1+radius, y2,
                 x1+radius, y2, x1, y2,
                 x1, y2-radius, x1, y2-radius,
                 x1, y2-radius, x1, y1+radius,
                 x1, y1+radius, x1, y1]
        return self.create_polygon(points, smooth=True, **kwargs)
    
    def on_enter(self, e):
        self.itemconfig(self.rect, fill=self.hover_color)
    
    def on_leave(self, e):
        self.itemconfig(self.rect, fill=self.default_color)

class ModernEntry(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=COLORS['bg_secondary'])
        
        self.entry = tk.Entry(self, 
                             font=('Consolas', 12),
                             bg=COLORS['bg_card'],
                             fg=COLORS['text_primary'],
                             insertbackground=COLORS['accent_cyan'],
                             relief='flat',
                             bd=0,
                             **kwargs)
        self.entry.pack(padx=2, pady=2, fill='both', expand=True)
        
        self.config(highlightbackground=COLORS['bg_card'], 
                   highlightthickness=2,
                   relief='flat')
        
        self.entry.bind('<FocusIn>', self.on_focus_in)
        self.entry.bind('<FocusOut>', self.on_focus_out)
    
    def on_focus_in(self, e):
        self.config(highlightbackground=COLORS['accent_cyan'])
    
    def on_focus_out(self, e):
        self.config(highlightbackground=COLORS['bg_card'])
    
    def get(self):
        return self.entry.get()
    
    def delete(self, first, last):
        return self.entry.delete(first, last)
    
    def insert(self, index, string):
        return self.entry.insert(index, string)
    
    def bind(self, *args, **kwargs):
        return self.entry.bind(*args, **kwargs)
    
    def focus_set(self):
        return self.entry.focus_set()

# --- 6. INTERFAZ GRÁFICA MEJORADA ---
class EDMasterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ED Master Pro 💫")
        self.root.geometry("1100x900")
        self.root.configure(bg=COLORS['bg_primary'])
        self.last_focused = None
        
        # Título principal
        header = tk.Frame(root, bg=COLORS['bg_primary'], height=80)
        header.pack(fill='x', padx=20, pady=(10, 0))
        header.pack_propagate(False)
        
        title_label = tk.Label(header, 
                              text="⚡ ED MASTER PRO ⚡",
                              font=('Segoe UI', 28, 'bold'),
                              bg=COLORS['bg_primary'],
                              fg=COLORS['accent_cyan'])
        title_label.pack(side='top', pady=5)
        
        subtitle = tk.Label(header,
                           text="Sistema Avanzado de Resolución de Ecuaciones Diferenciales",
                           font=('Segoe UI', 11),
                           bg=COLORS['bg_primary'],
                           fg=COLORS['text_secondary'])
        subtitle.pack(side='top')
        
        # Notebook
        style = ttk.Style()
        style.theme_use('default')
        
        style.configure('TNotebook', 
                       background=COLORS['bg_primary'],
                       borderwidth=0)
        style.configure('TNotebook.Tab',
                       background=COLORS['bg_secondary'],
                       foreground=COLORS['text_secondary'],
                       padding=[20, 10],
                       font=('Segoe UI', 10, 'bold'))
        style.map('TNotebook.Tab',
                 background=[('selected', COLORS['bg_card'])],
                 foreground=[('selected', COLORS['accent_cyan'])])
        
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill="both", padx=20, pady=10)
        
        self.tab_manual = tk.Frame(self.notebook, bg=COLORS['bg_secondary'])
        self.tab_lib = tk.Frame(self.notebook, bg=COLORS['bg_secondary'])
        self.tab_teoria = tk.Frame(self.notebook, bg=COLORS['bg_secondary'])
        
        self.notebook.add(self.tab_manual, text="  ⚙️  ENTRADA MANUAL  ")
        self.notebook.add(self.tab_lib, text="  📚  LIBRERÍA  ")
        self.notebook.add(self.tab_teoria, text="  📖  TEORÍA  ")
        
        self.setup_manual()
        self.setup_libreria()
        self.setup_teoria()
    
    def save_focus(self, entry):
        self.last_focused = entry
    
    def insert_symbol(self, sym):
        if sym == 'CLS':
            self.last_focused.delete(0, tk.END)
        else:
            self.last_focused.insert(tk.INSERT, sym)
            self.last_focused.focus_set()
    
    def crear_panel(self, parent):
        panel = tk.Frame(parent, bg=COLORS['bg_card'], relief='flat', bd=0)
        
        label = tk.Label(panel, 
                        text="🔢 PANEL MATEMÁTICO",
                        font=('Segoe UI', 11, 'bold'),
                        bg=COLORS['bg_card'],
                        fg=COLORS['text_primary'])
        label.pack(pady=10)
        
        btns_frame = tk.Frame(panel, bg=COLORS['bg_card'])
        btns_frame.pack(padx=15, pady=10)
        
        btns = [
            ('x','x'), ('y','y'), ('+','+'), ('-','-'), 
            ('x²','²'), ('^','^'), ('×','*'), ('÷','/'),
            ('(','('), (')',' )'), ('eˣ','exp('), ('ln','log('),
            ('sin','sin('), ('cos','cos('), ('√','sqrt('), ('⌫','CLS')
        ]
        
        for i, (txt, val) in enumerate(btns):
            bg_color = COLORS['error'] if val == 'CLS' else COLORS['bg_secondary']
            hover = COLORS['warning'] if val == 'CLS' else COLORS['hover']
            
            btn = ModernButton(btns_frame, txt, 
                             lambda v=val: self.insert_symbol(v),
                             width=65, height=35,
                             bg=bg_color, hover_bg=hover)
            btn.grid(row=i//8, column=i%8, padx=3, pady=3)
        
        return panel
    
    def setup_manual(self):
        container = tk.Frame(self.tab_manual, bg=COLORS['bg_secondary'])
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Card para M
        card_m = tk.Frame(container, bg=COLORS['bg_card'], relief='flat')
        card_m.pack(fill='x', pady=(0, 15))
        
        lbl_m = tk.Label(card_m, text="M(x,y) dx:", 
                        font=('Segoe UI', 12, 'bold'),
                        bg=COLORS['bg_card'],
                        fg=COLORS['accent_cyan'])
        lbl_m.pack(anchor='w', padx=15, pady=(10, 5))
        
        self.m_ent = ModernEntry(card_m, width=50)
        self.m_ent.pack(fill='x', padx=15, pady=(0, 10))
        self.m_ent.bind('<FocusIn>', lambda e: self.save_focus(self.m_ent))
        self.last_focused = self.m_ent
        
        # Card para N
        card_n = tk.Frame(container, bg=COLORS['bg_card'], relief='flat')
        card_n.pack(fill='x', pady=(0, 15))
        
        lbl_n = tk.Label(card_n, text="N(x,y) dy:", 
                        font=('Segoe UI', 12, 'bold'),
                        bg=COLORS['bg_card'],
                        fg=COLORS['accent_purple'])
        lbl_n.pack(anchor='w', padx=15, pady=(10, 5))
        
        self.n_ent = ModernEntry(card_n, width=50)
        self.n_ent.pack(fill='x', padx=15, pady=(0, 10))
        self.n_ent.bind('<FocusIn>', lambda e: self.save_focus(self.n_ent))
        
        # Panel matemático
        self.crear_panel(container).pack(fill='x', pady=15)
        
        # Botones de acción
        btn_frame = tk.Frame(container, bg=COLORS['bg_secondary'])
        btn_frame.pack(pady=15)
        
        ModernButton(btn_frame, "📊 PASO A PASO", 
                    self.solve_manual_text, width=200, height=45,
                    bg=COLORS['accent_blue']).pack(side='left', padx=5)
        
        ModernButton(btn_frame, "🤖 EXPLICACIÓN IA", 
                    self.solve_manual_ia, width=200, height=45,
                    bg=COLORS['accent_purple']).pack(side='left', padx=5)
        
        # Output
        output_frame = tk.Frame(container, bg=COLORS['bg_card'], relief='flat')
        output_frame.pack(fill='both', expand=True, pady=10)
        
        output_label = tk.Label(output_frame, text="📝 RESULTADO",
                               font=('Segoe UI', 11, 'bold'),
                               bg=COLORS['bg_card'],
                               fg=COLORS['text_primary'])
        output_label.pack(anchor='w', padx=15, pady=10)
        
        self.out_man = scrolledtext.ScrolledText(output_frame, 
                                                 height=12,
                                                 font=('Consolas', 10),
                                                 bg=COLORS['bg_primary'],
                                                 fg=COLORS['text_primary'],
                                                 insertbackground=COLORS['accent_cyan'],
                                                 relief='flat',
                                                 wrap=tk.WORD)
        self.out_man.pack(fill='both', expand=True, padx=15, pady=(0, 15))
    
    def setup_libreria(self):
        container = tk.Frame(self.tab_lib, bg=COLORS['bg_secondary'])
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Información de niveles
        info_frame = tk.Frame(container, bg=COLORS['bg_card'])
        info_frame.pack(fill='x', pady=(0, 15))
        
        info_label = tk.Label(info_frame,
                             text="💡 Selecciona un nivel de dificultad y un ejercicio para resolver",
                             font=('Segoe UI', 10),
                             bg=COLORS['bg_card'],
                             fg=COLORS['text_secondary'])
        info_label.pack(pady=10)
        
        # Contador de ejercicios
        self.count_label = tk.Label(info_frame,
                                    text=f"Total de ejercicios: {sum(len(v) for v in DB_EJERCICIOS.values())}",
                                    font=('Segoe UI', 9, 'bold'),
                                    bg=COLORS['bg_card'],
                                    fg=COLORS['accent_cyan'])
        self.count_label.pack(pady=(0, 10))
        
        # Selector de categoría
        card_cat = tk.Frame(container, bg=COLORS['bg_card'])
        card_cat.pack(fill='x', pady=(0, 10))
        
        tk.Label(card_cat, text="🏷️ Nivel de Dificultad:", 
                font=('Segoe UI', 11, 'bold'),
                bg=COLORS['bg_card'],
                fg=COLORS['text_primary']).pack(anchor='w', padx=15, pady=(10, 5))
        
        style = ttk.Style()
        style.configure('Modern.TCombobox',
                       fieldbackground=COLORS['bg_primary'],
                       background=COLORS['bg_card'],
                       foreground=COLORS['text_primary'])
        
        self.cat_cb = ttk.Combobox(card_cat, 
                                   values=list(DB_EJERCICIOS.keys()),
                                   state="readonly",
                                   font=('Segoe UI', 10),
                                   style='Modern.TCombobox')
        self.cat_cb.pack(fill='x', padx=15, pady=(0, 10))
        self.cat_cb.bind("<<ComboboxSelected>>", lambda e: self.update_ej_list())
        
        # Selector de ejercicio
        card_ej = tk.Frame(container, bg=COLORS['bg_card'])
        card_ej.pack(fill='x', pady=(0, 15))
        
        tk.Label(card_ej, text="📋 Ejercicio Específico:", 
                font=('Segoe UI', 11, 'bold'),
                bg=COLORS['bg_card'],
                fg=COLORS['text_primary']).pack(anchor='w', padx=15, pady=(10, 5))
        
        self.ej_cb = ttk.Combobox(card_ej, 
                                  state="readonly",
                                  font=('Consolas', 9),
                                  style='Modern.TCombobox')
        self.ej_cb.pack(fill='x', padx=15, pady=(0, 10))
        
        # Botón resolver
        ModernButton(container, "🚀 RESOLVER SELECCIONADO", 
                    self.solve_lib, width=250, height=45,
                    bg=COLORS['success']).pack(pady=15)
        
        # Output
        output_frame = tk.Frame(container, bg=COLORS['bg_card'])
        output_frame.pack(fill='both', expand=True, pady=10)
        
        tk.Label(output_frame, text="📊 SOLUCIÓN DETALLADA",
                font=('Segoe UI', 11, 'bold'),
                bg=COLORS['bg_card'],
                fg=COLORS['text_primary']).pack(anchor='w', padx=15, pady=10)
        
        self.out_lib = scrolledtext.ScrolledText(output_frame, 
                                                 height=15,
                                                 font=('Consolas', 9),
                                                 bg=COLORS['bg_primary'],
                                                 fg=COLORS['text_primary'],
                                                 relief='flat',
                                                 wrap=tk.WORD)
        self.out_lib.pack(fill='both', expand=True, padx=15, pady=(0, 15))
    
    def setup_teoria(self):
        container = tk.Frame(self.tab_teoria, bg=COLORS['bg_card'])
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        title = tk.Label(container,
                        text="📚 FUNDAMENTOS TEÓRICOS",
                        font=('Segoe UI', 16, 'bold'),
                        bg=COLORS['bg_card'],
                        fg=COLORS['accent_cyan'])
        title.pack(pady=15)
        
        txt = scrolledtext.ScrolledText(container, 
                                       wrap=tk.WORD,
                                       font=('Segoe UI', 10),
                                       bg=COLORS['bg_primary'],
                                       fg=COLORS['text_primary'],
                                       relief='flat',
                                       padx=20,
                                       pady=20)
        
        contenido = """
═══════════════════════════════════════════════════════════════════
  TEORÍA DE ECUACIONES DIFERENCIALES EXACTAS Y NO EXACTAS
═══════════════════════════════════════════════════════════════════

┌─ 1. ¿Qué es una ecuación diferencial? ─────────────────────────┐
│                                                                   │
│ Una ecuación diferencial es una relación matemática que vincula  │
│ una función desconocida con una o más de sus derivadas. En los   │
│ cursos introductorios se estudian principalmente ecuaciones       │
│ diferenciales de primer orden, en las cuales interviene          │
│ únicamente la primera derivada.                                  │
│                                                                   │
│ Forma general: M(x,y)dx + N(x,y)dy = 0                          │
└───────────────────────────────────────────────────────────────────┘

┌─ 2. Ecuación Diferencial Exacta ───────────────────────────────┐
│                                                                   │
│ Una ecuación M(x,y)dx + N(x,y)dy = 0 es EXACTA si existe una    │
│ función Ψ(x,y) tal que:                                          │
│                                                                   │
│    dΨ = M dx + N dy                                              │
│                                                                   │
│ CRITERIO: La ecuación es exacta si y solo si:                   │
│                                                                   │
│    ∂M/∂y = ∂N/∂x                                                │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘

┌─ 3. Método de Resolución (Ecuaciones Exactas) ─────────────────┐
│                                                                   │
│ Paso 1: Integrar M respecto a x                                  │
│         Ψ(x,y) = ∫M dx + h(y)                                    │
│                                                                   │
│ Paso 2: Derivar Ψ respecto a y e igualar a N                    │
│         ∂Ψ/∂y = N                                                │
│                                                                   │
│ Paso 3: Determinar h(y)                                          │
│         h'(y) = N - ∂(∫M dx)/∂y                                  │
│                                                                   │
│ Paso 4: Solución general                                         │
│         Ψ(x,y) = C                                               │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘

┌─ 4. Ecuaciones No Exactas ─────────────────────────────────────┐
│                                                                   │
│ Cuando ∂M/∂y ≠ ∂N/∂x, la ecuación NO es exacta.                 │
│                                                                   │
│ SOLUCIÓN: Buscar un factor integrante μ(x,y) tal que:           │
│                                                                   │
│    μ·M dx + μ·N dy = 0  SEA EXACTA                              │
│                                                                   │
│ Factores integrantes comunes:                                    │
│                                                                   │
│ • Si (∂M/∂y - ∂N/∂x)/N = f(x) → μ(x) = e^(∫f(x)dx)             │
│ • Si (∂N/∂x - ∂M/∂y)/M = g(y) → μ(y) = e^(∫g(y)dy)             │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘

┌─ 5. Ejemplo Completo ──────────────────────────────────────────┐
│                                                                   │
│ Resolver: (2x + y)dx + (x + 2y)dy = 0                           │
│                                                                   │
│ ✓ Verificar exactitud:                                           │
│   M = 2x + y    →  ∂M/∂y = 1                                    │
│   N = x + 2y    →  ∂N/∂x = 1                                    │
│   ∂M/∂y = ∂N/∂x  ✓ ES EXACTA                                    │
│                                                                   │
│ ✓ Integrar M:                                                    │
│   Ψ = ∫(2x + y)dx = x² + xy + h(y)                              │
│                                                                   │
│ ✓ Derivar y comparar:                                            │
│   ∂Ψ/∂y = x + h'(y) = x + 2y                                    │
│   h'(y) = 2y  →  h(y) = y²                                      │
│                                                                   │
│ ✓ Solución:                                                      │
│   x² + xy + y² = C                                               │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘

┌─ 6. Aplicaciones ──────────────────────────────────────────────┐
│                                                                   │
│ Las ecuaciones diferenciales exactas aparecen en:                │
│                                                                   │
│ • Física: Conservación de energía                                │
│ • Termodinámica: Funciones de estado                             │
│ • Mecánica: Campos conservativos                                 │
│ • Ingeniería: Circuitos eléctricos                               │
│ • Economía: Modelos de crecimiento                               │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════
"""
        txt.insert(tk.END, contenido)
        txt.config(state=tk.DISABLED)
        txt.pack(expand=True, fill='both', padx=10, pady=(0, 10))
    
    # --- MÉTODOS DE RESOLUCIÓN ---
    def update_ej_list(self):
        cat = self.cat_cb.get()
        ejercicios = DB_EJERCICIOS[cat]
        self.ej_cb['values'] = [e["desc"] for e in ejercicios]
        if ejercicios:
            self.ej_cb.current(0)
    
    def solve_lib(self):
        cat, desc = self.cat_cb.get(), self.ej_cb.get()
        if not cat or not desc:
            messagebox.showwarning("Advertencia", "⚠️ Selecciona categoría y ejercicio")
            return
        
        ej = next(e for e in DB_EJERCICIOS[cat] if e["desc"] == desc)
        
        # Mostrar mensaje de carga
        self.out_lib.delete(1.0, tk.END)
        self.out_lib.insert(tk.END, "🔄 Resolviendo ejercicio...\n\n")
        self.root.update()
        
        try:
            _, pasos = obtener_datos_completos_detallado(ej["M"], ej["N"])
            self.out_lib.delete(1.0, tk.END)
            self.out_lib.insert(tk.END, pasos)
        except Exception as e:
            messagebox.showerror("Error", f"❌ Error al resolver:\n{str(e)}")
    
    def solve_manual_text(self):
        m, n = pre_procesar_entrada(self.m_ent.get()), pre_procesar_entrada(self.n_ent.get())
        if not m or not n:
            messagebox.showwarning("Advertencia", "⚠️ Ingresa ambas funciones M y N")
            return
        
        # Mostrar mensaje de carga
        self.out_man.delete(1.0, tk.END)
        self.out_man.insert(tk.END, "🔄 Analizando ecuación diferencial...\n\n")
        self.root.update()
        
        try:
            _, pasos = obtener_datos_completos_detallado(m, n)
            self.out_man.delete(1.0, tk.END)
            self.out_man.insert(tk.END, pasos)
        except Exception as e:
            messagebox.showerror("Error", f"❌ Error al resolver:\n{str(e)}")
    
    def solve_manual_ia(self):
        m, n = pre_procesar_entrada(self.m_ent.get()), pre_procesar_entrada(self.n_ent.get())
        if not m or not n:
            messagebox.showwarning("Advertencia", "⚠️ Ingresa ambas funciones M y N")
            return
        
        self.out_man.delete(1.0, tk.END)
        self.out_man.insert(tk.END, "⏳ Conectando con Groq AI...\n\n🤖 Analizando la ecuación diferencial...\n")
        self.root.update()
        
        try:
            datos, pasos_detallados = obtener_datos_completos_detallado(m, n)
            
            # Crear prompt mejorado con los pasos detallados
            prompt = f"""Eres un profesor experto en ecuaciones diferenciales. He resuelto la siguiente ecuación y necesito que proporciones una explicación pedagógica clara y amigable.

ECUACIÓN ANALIZADA:


Por favor proporciona:
1. Una introducción amigable explicando qué tipo de ecuación es
2. Una explicación conceptual de por qué es importante verificar la exactitud
3. Procedimiento: Integración parcial y cálculo de h(y).
4. Explica paso a paso la resolución de:
        ({a_claro(datos['M'])})dx + ({a_claro(datos['N'])})dy = 0

Usa un tono motivador y educativo, como si estuvieras explicando a un estudiante en tu oficina."""

            res = client_groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2500
            )
            
            self.out_man.delete(1.0, tk.END)
            self.out_man.insert(tk.END, "═" * 70 + "\n")
            self.out_man.insert(tk.END, "  🤖 EXPLICACIÓN GENERADA POR INTELIGENCIA ARTIFICIAL\n")
            self.out_man.insert(tk.END, "═" * 70 + "\n\n")
            self.out_man.insert(tk.END, res.choices[0].message.content)
            self.out_man.insert(tk.END, "\n\n" + "═" * 70 + "\n")
            self.out_man.insert(tk.END, "\n💡 Consejo: Usa el botón 'PASO A PASO' para ver la resolución matemática detallada.\n")
            
        except Exception as e:
            messagebox.showerror("Error IA", f"❌ Error al conectar con Groq:\n{str(e)}")

# --- 7. EJECUCIÓN PRINCIPAL ---
if __name__ == "__main__":
    root = tk.Tk()
    app = EDMasterApp(root)
    root.mainloop()
