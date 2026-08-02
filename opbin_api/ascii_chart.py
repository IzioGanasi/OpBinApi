import sys
import math
from typing import List, Dict, Tuple, Optional


class BrailleCanvas:
    """
    Canvas Sub-Pixel de alta resolução utilizando a matriz Braille Unicode (2x4 pontos por caractere).
    Oferece 4x mais resolução vertical e 2x mais resolução horizontal que o terminal padrão.
    """
    MAP = [
        [0x01, 0x02, 0x04, 0x40],  # Coluna 0 (pontos 1, 2, 3, 7)
        [0x08, 0x10, 0x20, 0x80]   # Coluna 1 (pontos 4, 5, 6, 8)
    ]

    def __init__(self, char_width: int, char_height: int):
        self.char_width = char_width
        self.char_height = char_height
        self.pixel_width = char_width * 2
        self.pixel_height = char_height * 4

        self.grid = [[0 for _ in range(char_width)] for _ in range(char_height)]
        self.colors = [[None for _ in range(char_width)] for _ in range(char_height)]
        self.override_chars = {}

    def set_pixel(self, px: int, py: int, color: str = ""):
        if 0 <= px < self.pixel_width and 0 <= py < self.pixel_height:
            cx = px // 2
            cy = py // 4
            dot_x = px % 2
            dot_y = py % 4

            self.grid[cy][cx] |= self.MAP[dot_x][dot_y]
            if color:
                self.colors[cy][cx] = color

    def draw_line(self, x0: int, y0: int, x1: int, y1: int, color: str = ""):
        """Algoritmo de linha de Bresenham em resolução de sub-pixel."""
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        while True:
            self.set_pixel(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy


class AsciiChart:
    """
    Gerador de Gráficos Sub-Pixel de Alta Precisão em Estilo Calculadora Gráfica.
    Projetado para gráficos financeiros, indicadores técnicos e calculadoras no terminal.
    """
    RESET = "\033[0m"
    GREEN = "\033[1;32m"
    RED = "\033[1;31m"
    YELLOW = "\033[1;33m"
    CYAN = "\033[1;36m"
    MAGENTA = "\033[1;35m"
    WHITE = "\033[1;37m"
    GRAY = "\033[90m"

    @staticmethod
    def render(
        series: Dict[str, Tuple[List[float], str]], 
        height: int = 10, 
        width: int = 60,
        markers: Optional[List[Dict]] = None,
        title: Optional[str] = None,
        h_lines: Optional[List[Dict]] = None
    ) -> str:
        if hasattr(sys.stdout, "reconfigure"):
            try:
                sys.stdout.reconfigure(encoding="utf-8")
            except Exception:
                pass

        markers = markers or []
        h_lines = h_lines or []

        all_vals = []
        for name, (vals, _) in series.items():
            valid_vals = [v for v in vals if v is not None and not math.isnan(v)]
            all_vals.extend(valid_vals)

        for hl in h_lines:
            if "value" in hl and hl["value"] is not None:
                all_vals.append(hl["value"])

        if not all_vals:
            return ""

        min_val = min(all_vals)
        max_val = max(all_vals)

        if min_val == max_val:
            min_val -= 0.0001
            max_val += 0.0001

        val_range = max_val - min_val

        canvas = BrailleCanvas(width, height)

        def val_to_pixel_y(val: float) -> int:
            normalized = (val - min_val) / val_range
            py = int(round(normalized * (canvas.pixel_height - 1)))
            return max(0, min(canvas.pixel_height - 1, py))

        # 1. Linhas Horizontais de Referência (ex: Nível de Entrada da Ordem)
        for hl in h_lines:
            hl_val = hl.get("value")
            hl_color = hl.get("color", AsciiChart.GRAY)
            if hl_val is not None:
                py = canvas.pixel_height - 1 - val_to_pixel_y(hl_val)
                for px in range(0, canvas.pixel_width, 2):
                    canvas.set_pixel(px, py, hl_color)

        # 2. Curvas Contínuas em Alta Resolução Sub-Pixel (Bresenham)
        max_len = 1
        for name, (vals, color) in series.items():
            if not vals:
                continue

            max_len = max(max_len, len(vals))
            valid_pairs = []
            for i, v in enumerate(vals):
                if v is not None and not math.isnan(v):
                    px = int(i * (canvas.pixel_width - 1) / float(len(vals) - 1)) if len(vals) > 1 else 0
                    py = canvas.pixel_height - 1 - val_to_pixel_y(v)
                    valid_pairs.append((px, py))

            for k in range(len(valid_pairs) - 1):
                x0, y0 = valid_pairs[k]
                x1, y1 = valid_pairs[k + 1]
                canvas.draw_line(x0, y0, x1, y1, color)

        # 3. Marcadores Operacionais Sobrepostos (⬆ CALL / ⬇ PUT)
        for m in markers:
            idx = m.get("index")
            val = m.get("value")
            sym = m.get("symbol")
            if not sym:
                sym = "⬆" if m.get("direction") == "call" else "⬇"
            
            m_color = m.get("color", AsciiChart.WHITE)

            if idx is not None and val is not None:
                px = int(idx * (canvas.pixel_width - 1) / float(max_len - 1)) if max_len > 1 else 0
                py = canvas.pixel_height - 1 - val_to_pixel_y(val)
                cx = px // 2
                cy = py // 4
                if 0 <= cx < width and 0 <= cy < height:
                    canvas.override_chars[(cy, cx)] = (sym, m_color)

        # 4. Formata as linhas do Canvas com Eixo Y e Margens Elegantes
        output_lines = []

        if title:
            output_lines.append(f"{AsciiChart.WHITE}{title}{AsciiChart.RESET}")

        for r in range(height):
            y_fraction = (height - 1 - r) / float(height - 1)
            line_val = min_val + (y_fraction * val_range)

            if max_val > 1000:
                y_label = f"{line_val:8.2f}"
            elif max_val > 1:
                y_label = f"{line_val:8.4f}"
            else:
                y_label = f"{line_val:8.5f}"

            row_str = ""
            for c in range(width):
                if (r, c) in canvas.override_chars:
                    sym, col = canvas.override_chars[(r, c)]
                    row_str += f"{col}{sym}{AsciiChart.RESET}"
                else:
                    bits = canvas.grid[r][c]
                    color = canvas.colors[r][c] or AsciiChart.CYAN
                    
                    if bits > 0:
                        braille_char = chr(0x2800 + bits)
                        row_str += f"{color}{braille_char}{AsciiChart.RESET}"
                    else:
                        row_str += " "

            output_lines.append(f"{AsciiChart.GRAY}{y_label} │{AsciiChart.RESET}{row_str}")

        # Eixo X
        output_lines.append(f"{AsciiChart.GRAY}         └{'─' * width}{AsciiChart.RESET}")

        # Legenda
        legend_parts = []
        for name, (_, color) in series.items():
            legend_parts.append(f"{color}⠤⠤ {name}{AsciiChart.RESET}")

        for hl in h_lines:
            if "label" in hl:
                hl_color = hl.get("color", AsciiChart.GRAY)
                legend_parts.append(f"{hl_color}╌╌ {hl['label']}{AsciiChart.RESET}")

        if legend_parts:
            output_lines.append("   " + "   ".join(legend_parts))

        return "\n".join(output_lines)
