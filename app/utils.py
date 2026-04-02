# Steam Guide Downloader
# Copyright (c) 2025-2026 AlexAgents
# Licensed under the MIT License. See LICENSE file in the project root.

"""Utility functions"""

import re
import os
import logging

from docx.shared import RGBColor
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

logger = logging.getLogger(__name__)


def clean_filename(title: str) -> str:
    if not title:
        return ""
    cleaned = re.sub(r'[\\/*?:"<>|]', "", title)
    cleaned = re.sub(r'[\x00-\x1f\x7f]', "", cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    cleaned = cleaned[:200]
    cleaned = cleaned.rstrip('. ')
    return cleaned


def validate_save_path(path: str) -> tuple[bool, str]:
    if not path or not path.strip():
        return False, "Path is empty"

    path = path.strip()
    path = os.path.expanduser(path)
    path = os.path.expandvars(path)
    path = os.path.normpath(path)

    if os.name == 'nt':
        invalid_chars = re.findall(r'[*?"<>|]', path)
        if invalid_chars:
            return False, f"Invalid characters: {''.join(set(invalid_chars))}"

    if os.path.exists(path):
        if not os.path.isdir(path):
            return False, "Path is not a directory"
        if not os.access(path, os.W_OK):
            return False, "Directory is not writable"
        return True, path

    try:
        os.makedirs(path, exist_ok=True)
        return True, path
    except OSError as e:
        return False, f"Cannot create directory: {e}"


def add_horizontal_line(paragraph):
    try:
        pPr = paragraph._p.get_or_add_pPr()
        pBdr = OxmlElement('w:pBdr')
        bottom = OxmlElement('w:bottom')
        bottom.set(qn('w:val'), 'single')
        bottom.set(qn('w:sz'), '6')
        bottom.set(qn('w:space'), '1')
        bottom.set(qn('w:color'), 'auto')
        pBdr.append(bottom)
        pPr.append(pBdr)
    except Exception as e:
        logger.warning(f"Horizontal line error: {e}")


def add_hyperlink(paragraph, url, text, color=None, underline=True):
    if color is None:
        color = RGBColor(0x05, 0x63, 0xC1)

    if not url:
        return paragraph.add_run(text)

    try:
        part = paragraph.part
        r_id = part.relate_to(
            url,
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
            is_external=True
        )

        hyperlink = OxmlElement('w:hyperlink')
        hyperlink.set(qn('r:id'), r_id)

        new_run = OxmlElement('w:r')
        rPr = OxmlElement('w:rPr')

        if color:
            c_elem = OxmlElement('w:color')
            if isinstance(color, RGBColor):
                color_str = str(color)
            elif hasattr(color, 'rgb'):
                color_str = str(color.rgb)
            else:
                color_str = "0563C1"
            c_elem.set(qn('w:val'), color_str)
            rPr.append(c_elem)

        if underline:
            u = OxmlElement('w:u')
            u.set(qn('w:val'), 'single')
            rPr.append(u)

        new_run.append(rPr)
        new_run.text = text
        hyperlink.append(new_run)
        paragraph._p.append(hyperlink)
        return hyperlink

    except Exception as e:
        logger.warning(f"Hyperlink error '{url}': {e}")
        run = paragraph.add_run(text)
        if color and isinstance(color, RGBColor):
            run.font.color.rgb = color
        return run