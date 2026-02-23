from .constants import BLOCK_HEIGHT_PIXEL, BLOCK_WIDTH_PIXEL, COLOR_BG, COLOR_HEADER, DATA_HEIGHT, FONT_SIZE_DATA, HEADER_HEIGHT


def get_coverage_label(c_r, c_l):
    rf_percent = (1.0 - c_r) * 100
    lat_percent = (1.0 - c_l) * 100

    width_total = int(BLOCK_WIDTH_PIXEL)
    cell_width = width_total // 2

    return (
        f'<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" WIDTH="{width_total}" '
        f'HEIGHT="{BLOCK_HEIGHT_PIXEL}" FIXEDSIZE="TRUE">'
        f"<TR>"
        f'<TD PORT="rf" WIDTH="{cell_width}" HEIGHT="{DATA_HEIGHT}" '
        f'BGCOLOR="{COLOR_BG}"><FONT POINT-SIZE="{FONT_SIZE_DATA}">'
        f"{rf_percent:.1f}%</FONT></TD>"
        f'<TD PORT="latent" WIDTH="{cell_width}" HEIGHT="{DATA_HEIGHT}" '
        f'BGCOLOR="{COLOR_BG}"><FONT POINT-SIZE="{FONT_SIZE_DATA}">'
        f"{lat_percent:.1f}%</FONT></TD>"
        f"</TR>"
        f"<TR>"
        f'<TD COLSPAN="2" WIDTH="{width_total}" HEIGHT="{HEADER_HEIGHT}" '
        f'BGCOLOR="{COLOR_HEADER}"><B>Coverage</B></TD>'
        f"</TR></TABLE>>"
    )
