"""
Bridge between the JavaScript frontend and the Python design engine.
"""

from __future__ import annotations

import base64
import io
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from core.bom import encode_file_response, generate_bom_items, generate_excel_bom, generate_ga_pdf, generate_pdf_report
from core.constants import FALLBACK_MCCB_DB, STANDARD_MCCBS
from core.ga import compute_panel_dimensions, generate_ga_svg
from core.sld import SystemCalculations, generate_sld
from core.utils import (
    calculate_current_from_kva,
    calculate_current_from_power,
    get_busbar_chamber_height,
    get_busbar_thickness,
    get_mccb_dims,
    get_standard_rating,
    get_theme_colors,
    generate_busbar_spec,
    load_mccb_dimensions_from_file,
)


def _as_int(value, default=0):
    try:
        return int(float(value))
    except Exception:
        return default


def _as_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def _normalize_list(values, length, default):
    items = list(values or [])
    if len(items) < length:
        items.extend([default] * (length - len(items)))
    return items[:length]


class MicrogridBridge:
    """Stateful API exposed to the pywebview frontend."""

    def __init__(self):
        self.theme = "dark"
        self.mccb_db = {}
        self.last_payload = self._default_payload()

    def _default_payload(self):
        return {
            "solar_kw": 100,
            "grid_kw": 120,
            "num_dg": 2,
            "dg_ratings": [250, 250],
            "num_outputs": 3,
            "outgoing_ratings": [400, 400, 250],
            "busbar_material": "Aluminium",
            "num_poles": 4,
        }

    def _active_db(self):
        return self.mccb_db or FALLBACK_MCCB_DB

    def get_state(self):
        payload = dict(self.last_payload)
        payload["theme"] = self.theme
        payload["mccb_loaded"] = bool(self.mccb_db)
        payload["mccb_count"] = len(self.mccb_db)
        payload["mccb_preview"] = self._mccb_preview()
        return payload

    def set_theme(self, theme):
        if theme in ("dark", "light"):
            self.theme = theme
        return {"ok": True, "theme": self.theme}

    def load_mccb_database(self, file_name, data_base64):
        try:
            raw_bytes = base64.b64decode(data_base64)
            buffer = io.BytesIO(raw_bytes)
            db_loaded = load_mccb_dimensions_from_file(uploaded_file=buffer)
            if db_loaded:
                self.mccb_db = db_loaded
                return {
                    "ok": True,
                    "file_name": file_name,
                    "count": len(db_loaded),
                    "preview": self._mccb_preview(),
                }
            return {"ok": False, "error": "Could not parse MCCB workbook. Check the format."}
        except Exception as error:
            return {"ok": False, "error": str(error)}

    def generate(self, payload=None):
        try:
            design = self._compute_design(payload or self.last_payload)
            self.last_payload = dict(design["inputs"])
            self.last_payload["theme"] = self.theme
            response = dict(design)
            response["bom_objects"] = design["bom_rows"]
            return response
        except Exception as error:
            return {"ok": False, "error": str(error)}

    def export_pdf(self, payload=None):
        try:
            design = self._compute_design(payload or self.last_payload)
            pdf_buffer = generate_pdf_report(
                design["sld"]["svg"],
                design["sld"]["width"],
                design["sld"]["height"],
                design["ga"]["svg"],
                design["ga"]["width"],
                design["ga"]["height"],
                design["incomer_list"],
                design["mccb_outputs"],
                design["bom_objects"],
                design["inputs"]["solar_kw"],
                design["inputs"]["grid_kw"],
                design["inputs"]["num_dg"],
                design["inputs"]["num_outputs"],
                design["summary"]["total_busbar_current"],
                design["summary"]["total_outgoing_rating"],
                design["summary"]["busbar_spec"],
                design["ga"]["panel_w"],
                design["ga"]["panel_h"],
                design["ga"]["panel_d"],
                design["inputs"]["num_poles"],
                self._active_db(),
                design["summary"]["warning_flag"],
            )
            return self._save_export_file(
                pdf_buffer.getvalue(),
                "microgrid_panel_report.pdf",
                ("PDF Files (*.pdf)",),
            )
        except Exception as error:
            return {"ok": False, "error": str(error)}

    def export_ga_pdf(self, payload=None):
        try:
            design = self._compute_design(payload or self.last_payload)
            pdf_buffer = generate_ga_pdf(
                design["ga"]["svg"],
                design["ga"]["width"],
                design["ga"]["height"],
                design["incomer_list"],
                design["mccb_outputs"],
                design["ga"]["panel_w"],
                design["ga"]["panel_h"],
                design["ga"]["panel_d"],
                design["inputs"]["num_poles"],
                self._active_db(),
            )
            return self._save_export_file(
                pdf_buffer.getvalue(),
                "microgrid_panel_ga.pdf",
                ("PDF Files (*.pdf)",),
            )
        except Exception as error:
            return {"ok": False, "error": str(error)}

    def export_excel(self, payload=None):
        try:
            design = self._compute_design(payload or self.last_payload)
            excel_bytes = generate_excel_bom(design["bom_objects"])
            return self._save_export_file(
                excel_bytes,
                "microgrid_panel_bom.xlsx",
                ("Excel Workbook (*.xlsx)",),
            )
        except Exception as error:
            return {"ok": False, "error": str(error)}

    def _save_export_file(self, data_bytes, default_filename, file_types):
        try:
            import webview

            if not webview.windows:
                return {"ok": False, "error": "Application window is not available."}

            dialog_result = webview.windows[0].create_file_dialog(
                webview.FileDialog.SAVE,
                save_filename=default_filename,
                file_types=file_types,
            )
            if not dialog_result:
                return {"ok": False, "error": "Save cancelled."}

            target_path = Path(dialog_result[0])
            target_path.write_bytes(data_bytes)
            return {"ok": True, "filename": target_path.name, "path": str(target_path)}
        except Exception as error:
            return {"ok": False, "error": str(error)}

    def _mccb_preview(self, limit=20):
        preview = []
        for rating in sorted(self._active_db().keys())[:limit]:
            dims = self._active_db()[rating]
            preview.append(
                {
                    "rating": rating,
                    "height": dims["h"],
                    "width": dims["w"],
                    "depth": dims["d"],
                    "frame": dims["frame"],
                }
            )
        return preview

    def _compute_design(self, payload):
        theme = payload.get("theme", self.theme)
        solar_kw = _as_float(payload.get("solar_kw", 0))
        grid_kw = _as_float(payload.get("grid_kw", 0))
        num_dg = max(0, _as_int(payload.get("num_dg", 0)))
        num_outputs = max(1, _as_int(payload.get("num_outputs", 1)))
        num_poles = _as_int(payload.get("num_poles", 4), 4)
        busbar_material = payload.get("busbar_material", "Copper")

        dg_ratings = _normalize_list(payload.get("dg_ratings", []), num_dg, 0)
        outgoing_ratings = _normalize_list(payload.get("outgoing_ratings", []), num_outputs, 250)

        dg_ratings = [_as_float(value, 0) for value in dg_ratings]
        outgoing_ratings = [_as_float(value, 0) for value in outgoing_ratings]

        mccb_outputs = [get_standard_rating(value) for value in outgoing_ratings]
        system_calcs = SystemCalculations(solar_kw=solar_kw, grid_kw=grid_kw, dg_ratings_kva=dg_ratings)

        incomer_list = list(system_calcs.dg_mccbs)
        if grid_kw > 0:
            incomer_list.append(system_calcs.mccb_grid)
        if solar_kw > 0:
            incomer_list.append(system_calcs.mccb_solar)

        total_busbar_current = system_calcs.total_busbar_current
        total_outgoing_rating = sum(mccb_outputs)
        warning_flag = total_busbar_current > total_outgoing_rating
        busbar_spec = generate_busbar_spec(total_busbar_current, busbar_material)

        active_db = self._active_db()
        ga_svg_str, ga_svg_w, ga_svg_h, panel_w, panel_h, panel_d = generate_ga_svg(
            incomer_list,
            mccb_outputs,
            total_busbar_current,
            busbar_spec,
            num_poles,
            busbar_material,
            active_db,
            theme=theme,
        )

        theme_colors = get_theme_colors(theme)
        sld_svg, sld_svg_w, sld_svg_h = generate_sld(
            system_calcs,
            num_outputs,
            mccb_outputs,
            num_poles,
            num_dg,
            grid_kw,
            solar_kw,
            total_busbar_current,
            theme_colors["svg_bg"],
            theme_colors["text"],
            theme_colors["svg_stroke"],
            theme_colors["subtitle"],
        )

        bom_objects = generate_bom_items(
            solar_kw,
            grid_kw,
            num_dg,
            system_calcs.dg_mccbs,
            system_calcs.mccb_solar,
            system_calcs.mccb_grid,
            mccb_outputs,
            num_poles,
            busbar_spec,
            total_busbar_current,
            busbar_material,
            panel_h,
            panel_w,
            panel_d,
        )

        bom_rows = []
        for index, item in enumerate(bom_objects, 1):
            row = item.to_dict()
            row["Sr No"] = index
            bom_rows.append(row)

        schedule_rows = []
        for index, rating in enumerate(incomer_list, 1):
            dims = get_mccb_dims(rating, active_db)
            schedule_rows.append(
                {
                    "tag": f"I/C {index}",
                    "description": "Incomer MCCB",
                    "rating": f"{rating}A",
                    "poles": f"{num_poles}P",
                    "dimensions": f"{dims['h']}×{dims['w']}×{dims['d']}",
                    "frame": dims["frame"],
                }
            )
        for index, rating in enumerate(mccb_outputs, 1):
            dims = get_mccb_dims(rating, active_db)
            schedule_rows.append(
                {
                    "tag": f"O/G {index}",
                    "description": "Outgoing MCCB",
                    "rating": f"{rating}A",
                    "poles": f"{num_poles}P",
                    "dimensions": f"{dims['h']}×{dims['w']}×{dims['d']}",
                    "frame": dims["frame"],
                }
            )

        return {
            "ok": True,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "inputs": {
                "theme": theme,
                "solar_kw": solar_kw,
                "grid_kw": grid_kw,
                "num_dg": num_dg,
                "dg_ratings": dg_ratings,
                "num_outputs": num_outputs,
                "outgoing_ratings": outgoing_ratings,
                "busbar_material": busbar_material,
                "num_poles": num_poles,
            },
            "summary": {
                "i_solar": system_calcs.i_solar,
                "i_grid": system_calcs.i_grid,
                "dg_currents": system_calcs.dg_currents,
                "dg_mccbs": system_calcs.dg_mccbs,
                "mccb_solar": system_calcs.mccb_solar,
                "mccb_grid": system_calcs.mccb_grid,
                "total_busbar_current": total_busbar_current,
                "total_outgoing_rating": total_outgoing_rating,
                "busbar_spec": busbar_spec,
                "warning_flag": warning_flag,
                "busbar_chamber_height": get_busbar_chamber_height(total_busbar_current),
                "busbar_thickness": get_busbar_thickness(total_busbar_current),
                "standard_mccbs": STANDARD_MCCBS,
            },
            "sld": {
                "svg": sld_svg,
                "width": sld_svg_w,
                "height": sld_svg_h,
            },
            "ga": {
                "svg": ga_svg_str,
                "width": ga_svg_w,
                "height": ga_svg_h,
                "panel_w": panel_w,
                "panel_h": panel_h,
                "panel_d": panel_d,
            },
            "incomer_list": incomer_list,
            "mccb_outputs": mccb_outputs,
            "bom_rows": bom_rows,
            "bom_objects": bom_objects,
            "schedule_rows": schedule_rows,
            "mccb_preview": self._mccb_preview(),
        }
