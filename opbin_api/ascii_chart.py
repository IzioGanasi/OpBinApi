import sys
import math
from typing import List, Dict, Tuple, Optional


class AsciiChart:
    """
    Biblioteca de renderização de gráficos ASCII / Unicode de ALTA CONTINUIDADE E PRECISÃO.
    Projetada especificamente para o mercado financeiro com suporte a linhas 100% contínuas,
    camadas de cores dedicadas (sem apagamento de cores por sobreposição), linhas de preço
    de entrada e marcadores de Call/Put/Cruzamentos (⬆ ⬇ ✕).
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
        """
        Renderiza um gráfico ASCII colorido de linhas 100% contínuas e sem buracos.
        """
        if hasattr(sys.stdout, "reconfigure"):
            try:
                sys.stdout.reconfigure(encoding="utf-8")
            except Exception:
                pass

        markers = markers or []
        h_lines = h_lines or []

        # 1. Coleta amplitude min/max para escala uniforme no eixo Y
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

        def val_to_y(val: float) -> int:
            normalized = (val - min_val) / val_range
            y = int(round(normalized * (height - 1)))
            return max(0, min(height - 1, y))

        # 2. Renderiza cada série em sua própria camada de cor dedicada (Garantia de Zero Buracos)
        layers = {}
        max_points = 1

        for name, (vals, color) in series.items():
            if not vals:
                continue

            num_p = len(vals)
            max_points = max(max_points, num_p)
            step = num_p / float(width) if num_p > width else 1.0

            layer_grid = [[" " for _ in range(width)] for _ in range(height)]
            prev_y = None

            for x in range(width):
                data_idx = int(x * step) if num_p > width else min(x, num_p - 1)
                val = vals[data_idx]
                if val is None or math.isnan(val):
                    continue

                y = val_to_y(val)
                row = height - 1 - y

                # Seleciona o caractere de tendência
                if prev_y is not None:
                    if y > prev_y:
                        char = "╱"
                    elif y < prev_y:
                        char = "╲"
                    else:
                        char = "─"
                else:
                    char = "─"

                layer_grid[row][x] = f"{color}{char}{AsciiChart.RESET}"

                # Preenche conexões verticais contínuas em variações bruscas (Sem falhas nem buracos)
                if prev_y is not None and abs(y - prev_y) > 1:
                    step_y = 1 if y > prev_y else -1
                    for fill_y in range(prev_y + step_y, y, step_y):
                        fill_row = height - 1 - fill_y
                        fill_char = "│" if fill_y != y and fill_y != prev_y else ("╱" if step_y > 0 else "╲")
                        layer_grid[fill_row][x] = f"{color}{fill_char}{AsciiChart.RESET}"

                prev_y = y

            layers[name] = layer_grid

        # 3. Desenha Linhas Horizontais de Referência (Preço de Entrada / Suporte / Resistência)
        hline_grid = [[" " for _ in range(width)] for _ in range(height)]
        for hl in h_lines:
            hl_val = hl.get("value")
            hl_color = hl.get("color", AsciiChart.GRAY)
            if hl_val is not None:
                y = val_to_y(hl_val)
                row = height - 1 - y
                for x in range(width):
                    hline_grid[row][x] = f"{hl_color}╌{AsciiChart.RESET}"

        # 4. Desenha Marcadores de Entrada de Operação (⬆ CALL / ⬇ PUT)
        marker_grid = [[" " for _ in range(width)] for _ in range(height)]
        for m in markers:
            idx = m.get("index")
            val = m.get("value")
            sym = m.get("symbol")
            if not sym:
                sym = "⬆" if m.get("direction") == "call" else "⬇"
            
            m_color = m.get("color", AsciiChart.WHITE)

            if idx is not None and val is not None:
                x = int(idx * (width / float(max_points))) if max_points > width else idx
                if 0 <= x < width:
                    y = val_to_y(val)
                    row = height - 1 - y
                    marker_grid[row][x] = f"{m_color}{sym}{AsciiChart.RESET}"

        # 5. Mescla todas as camadas na grade final destacando cruzamentos (✕)
        final_grid = [[" " for _ in range(width)] for _ in range(height)]

        # Aplica linhas horizontais de fundo
        for r in range(height):
            for c in range(width):
                if hline_grid[r][c] != " ":
                    final_grid[r][c] = hline_grid[r][c]

        # Aplica séries numéricas (com detecção de interseções / cruzamentos)
        for name, layer in layers.items():
            for r in range(height):
                for c in range(width):
                    if layer[r][c] != " ":
                        if final_grid[r][c] != " " and final_grid[r][c] != layer[r][c] and "╌" not in final_grid[r][c]:
                            # Interseção de linhas -> destaca o ponto de cruzamento exato!
                            final_grid[r][c] = f"{AsciiChart.WHITE}✕{AsciiChart.RESET}"
                        else:
                            final_grid[r][c] = layer[r][c]

        # Aplica marcadores operacionais no topo
        for r in range(height):
            for c in range(width):
                if marker_grid[r][c] != " ":
                    final_grid[r][c] = marker_grid[r][c]

        # 6. Monta a saída final com Eixo Y e Legenda
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

            row_str = "".join(final_grid[r])
            output_lines.append(f"{AsciiChart.GRAY}{y_label} │{AsciiChart.RESET}{row_str}")

        # Eixo X
        output_lines.append(f"{AsciiChart.GRAY}         └{'─' * width}{AsciiChart.RESET}")

        # Legenda
        legend_parts = []
        for name, (_, color) in series.items():
            legend_parts.append(f"{color}── {name}{AsciiChart.RESET}")

        for hl in h_lines:
            if "label" in hl:
                hl_color = hl.get("color", AsciiChart.GRAY)
                legend_parts.append(f"{hl_color}╌╌ {hl['label']}{AsciiChart.RESET}")

        if legend_parts:
            output_lines.append("   " + "   ".join(legend_parts))

        return "\n".join(output_lines)
