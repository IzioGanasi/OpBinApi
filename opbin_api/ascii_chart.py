import sys
import math
from typing import List, Dict, Tuple, Optional


def _supports_utf8() -> bool:
    """Verifica se o ambiente atual suporta caracteres Unicode/UTF-8 no terminal."""
    encoding = getattr(sys.stdout, "encoding", "") or ""
    return "utf" in encoding.lower() or "utf-8" in encoding.lower()


class AsciiChart:
    """
    Biblioteca de renderização de gráficos ASCII / Unicode em alta definição para terminal.
    Projetada especificamente para o mercado financeiro com suporte a múltiplas linhas,
    linhas de preço de entrada, marcadores de Call/Put e ANSI colors.
    """
    
    # Cores ANSI
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
        """
        Renderiza um gráfico ASCII colorido de alta precisão.
        
        :param series: Dicionário {"NomeLinha": (lista_de_valores, codigo_cor_ansi)}
        :param height: Altura em linhas de terminal
        :param width: Largura em colunas
        :param markers: Marcadores de eventos [{"index": 12, "symbol": "⬆", "color": "\033[1;32m", "label": "CALL"}]
        :param title: Título opcional do gráfico
        :param h_lines: Linhas horizontais de referência [{"value": 1.1650, "color": "\033[1;33m", "label": "Ordem"}]
        """
        if hasattr(sys.stdout, "reconfigure"):
            try:
                sys.stdout.reconfigure(encoding="utf-8")
            except Exception:
                pass

        use_utf = _supports_utf8()

        # Caracteres adaptativos conforme capacidade do terminal
        c_up = "╱" if use_utf else "/"
        c_down = "╲" if use_utf else "\\"
        c_flat = "─" if use_utf else "-"
        c_point = "•" if use_utf else "*"
        c_hline = "╌" if use_utf else "-"
        c_cross = "┼" if use_utf else "+"
        c_corner = "└" if use_utf else "+"

        if not series:
            return ""

        markers = markers or []
        h_lines = h_lines or []

        # Determina o menor e maior valor para escala no eixo Y
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

        # Prepara a grade (matrix 2D de caracteres)
        grid = [[" " for _ in range(width)] for _ in range(height)]
        color_grid = [[AsciiChart.RESET for _ in range(width)] for _ in range(height)]

        def val_to_y(val: float) -> int:
            normalized = (val - min_val) / val_range
            y = int(round(normalized * (height - 1)))
            return max(0, min(height - 1, y))

        # 1. Linhas Horizontais de Referência
        for hl in h_lines:
            hl_val = hl.get("value")
            hl_color = hl.get("color", AsciiChart.GRAY)
            if hl_val is not None:
                y = val_to_y(hl_val)
                row = height - 1 - y
                for x in range(width):
                    grid[row][x] = c_hline
                    color_grid[row][x] = hl_color

        # 2. Séries de Linhas
        num_points = 1
        for name, (vals, color) in series.items():
            if not vals:
                continue

            num_points = max(num_points, len(vals))
            step = len(vals) / float(width) if len(vals) > width else 1.0

            for x in range(width):
                data_idx = int(x * step) if len(vals) > width else x
                if data_idx >= len(vals):
                    break

                val = vals[data_idx]
                if val is None or math.isnan(val):
                    continue

                y = val_to_y(val)
                row = height - 1 - y

                if data_idx < len(vals) - 1 and vals[data_idx + 1] is not None:
                    next_y = val_to_y(vals[data_idx + 1])
                    if next_y > y:
                        char = c_up
                    elif next_y < y:
                        char = c_down
                    else:
                        char = c_flat
                else:
                    char = c_point

                grid[row][x] = char
                color_grid[row][x] = color

        # 3. Marcadores (⬆ CALL, ⬇ PUT, • Sinal)
        for m in markers:
            idx = m.get("index")
            val = m.get("value")
            sym = m.get("symbol")
            if not sym:
                sym = ("⬆" if use_utf else "^") if m.get("direction") == "call" else ("⬇" if use_utf else "v")
            
            m_color = m.get("color", AsciiChart.WHITE)

            if idx is not None:
                x = int(idx * (width / float(num_points))) if num_points > width else idx
                if 0 <= x < width:
                    y = val_to_y(val) if val is not None else 0
                    row = height - 1 - y
                    grid[row][x] = sym
                    color_grid[row][x] = m_color

        # 4. Monta Saída com Eixo Y
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
                cell_char = grid[r][c]
                cell_color = color_grid[r][c]
                row_str += f"{cell_color}{cell_char}{AsciiChart.RESET}"

            output_lines.append(f"{AsciiChart.GRAY}{y_label} {c_cross}{AsciiChart.RESET}{row_str}")

        # Eixo X
        output_lines.append(f"{AsciiChart.GRAY}         {c_corner}{c_flat * width}{AsciiChart.RESET}")

        # Legenda
        legend_parts = []
        for name, (_, color) in series.items():
            legend_parts.append(f"{color}{c_flat * 2} {name}{AsciiChart.RESET}")
        
        for hl in h_lines:
            if "label" in hl:
                hl_color = hl.get("color", AsciiChart.GRAY)
                legend_parts.append(f"{hl_color}{c_hline * 2} {hl['label']}{AsciiChart.RESET}")

        if legend_parts:
            output_lines.append("   " + "   ".join(legend_parts))

        return "\n".join(output_lines)
