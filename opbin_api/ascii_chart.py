import sys
import math
from typing import List, Dict, Tuple, Optional


class BrailleCanvas:
    """
    Canvas Sub-Pixel de alta resolução (2x4 pontos por caractere Braille Unicode U+2800 - U+28FF).
    Oferece 4x mais resolução vertical e 2x mais resolução horizontal, criando curvas suaves e contínuas.
    """
    MAP = [
        [0x01, 0x02, 0x04, 0x40],  # Coluna 0 (pontos 1, 2, 3, 7)
        [0x08, 0x10, 0x20, 0x80]   # Coluna 1 (pontos 4, 5, 6, 8)
    ]

    def __init__(self, char_w: int, char_h: int):
        self.cw = char_w
        self.ch = char_h
        self.pw = char_w * 2
        self.ph = char_h * 4

    def draw_line_to_grid(self, grid: list, x0: int, y0: int, x1: int, y1: int):
        """Desenha uma linha contínua de sub-pixel na matriz de bits."""
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        while True:
            if 0 <= x0 < self.pw and 0 <= y0 < self.ph:
                cx = x0 // 2
                cy = y0 // 4
                dot_x = x0 % 2
                dot_y = y0 % 4
                grid[cy][cx] |= self.MAP[dot_x][dot_y]

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
    Gerador de Gráficos de Curvas Suaves Sub-Pixel (Estilo Calculadora Gráfica / TI-84).
    Linhas 100% contínuas, arredondadas e de alta resolução sem bordas ásperas.
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

        # 1. Coleta a escala Y global
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

        def val_to_py(val: float) -> int:
            norm = (val - min_val) / val_range
            py = int(round(norm * (canvas.ph - 1)))
            return max(0, min(canvas.ph - 1, py))

        # 2. Renderiza cada série em sua própria matriz de bits com sua cor dedicada
        layer_grids = {}
        layer_colors = {}
        max_points = 1

        for name, (vals, color) in series.items():
            if not vals:
                continue

            max_points = max(max_points, len(vals))
            grid = [[0 for _ in range(width)] for _ in range(height)]
            
            pts = []
            for i, v in enumerate(vals):
                if v is not None and not math.isnan(v):
                    px = int(round(i * (canvas.pw - 1) / float(len(vals) - 1))) if len(vals) > 1 else 0
                    py = canvas.ph - 1 - val_to_py(v)
                    pts.append((px, py))

            # Conecta os pontos vizinhos com sub-pixels contínuos
            for k in range(len(pts) - 1):
                canvas.draw_line_to_grid(grid, pts[k][0], pts[k][1], pts[k + 1][0], pts[k + 1][1])

            layer_grids[name] = grid
            layer_colors[name] = color

        # 3. Processa Linhas Horizontais de Referência (Preço da Ordem)
        hline_grid = [[" " for _ in range(width)] for _ in range(height)]
        for hl in h_lines:
            hl_val = hl.get("value")
            hl_color = hl.get("color", AsciiChart.GRAY)
            if hl_val is not None:
                py = canvas.ph - 1 - val_to_py(hl_val)
                row = py // 4
                for col in range(width):
                    hline_grid[row][col] = f"{hl_color}╌{AsciiChart.RESET}"

        # 4. Processa Marcadores Operacionais (⬆ CALL / ⬇ PUT)
        marker_grid = [[" " for _ in range(width)] for _ in range(height)]
        for m in markers:
            idx = m.get("index")
            val = m.get("value")
            sym = m.get("symbol")
            if not sym:
                sym = "⬆" if m.get("direction") == "call" else "⬇"
            
            m_color = m.get("color", AsciiChart.WHITE)

            if idx is not None and val is not None:
                px = int(round(idx * (canvas.pw - 1) / float(max_points - 1))) if max_points > 1 else 0
                py = canvas.ph - 1 - val_to_py(val)
                col = px // 2
                row = py // 4
                if 0 <= col < width and 0 <= row < height:
                    marker_grid[row][col] = f"{m_color}{sym}{AsciiChart.RESET}"

        # 5. Mescla as camadas no buffer do terminal usando exclusivamente as cores das séries
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
                # Prioridade 1: Marcadores Operacionais (⬆ / ⬇)
                if marker_grid[r][c] != " ":
                    row_str += marker_grid[r][c]
                    continue

                # Prioridade 2: Posição de Curvas Braille (Preserva 100% as cores originais da série)
                active_series = []
                combined_bits = 0
                for s_name, grid in layer_grids.items():
                    if grid[r][c] > 0:
                        active_series.append(s_name)
                        combined_bits |= grid[r][c]

                if combined_bits > 0:
                    braille_char = chr(0x2800 + combined_bits)
                    col = layer_colors[active_series[0]]
                    row_str += f"{col}{braille_char}{AsciiChart.RESET}"
                    continue

                # Prioridade 3: Linha de Nível de Preço da Ordem
                if hline_grid[r][c] != " ":
                    row_str += hline_grid[r][c]
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
