# Steam Guide Downloader
# Copyright (c) 2025-2026 AlexAgents
# Licensed under the MIT License. See LICENSE file in the project root.

"""
DOCX -> PDF conversion
Supports: LibreOffice, MS Word (win32com), comtypes, docx2pdf
Dynamic timeout based on file size.
"""

import os
import sys
import subprocess
import logging
import shutil

logger = logging.getLogger(__name__)

# Base timeout + per-MB factor for dynamic calculation
_BASE_TIMEOUT = 120
_TIMEOUT_PER_MB = 30
_MIN_TIMEOUT = 120
_MAX_TIMEOUT = 900


def _compute_timeout(docx_path: str, user_timeout: int = 300) -> int:
    """Compute dynamic timeout based on file size and user setting."""
    try:
        size_mb = os.path.getsize(docx_path) / (1024 * 1024)
        computed = int(_BASE_TIMEOUT + size_mb * _TIMEOUT_PER_MB)
        computed = max(_MIN_TIMEOUT, min(computed, _MAX_TIMEOUT))
        return max(computed, user_timeout)
    except OSError:
        return max(_MIN_TIMEOUT, user_timeout)


def check_available_converters() -> dict[str, bool]:
    result = {
        "libreoffice": False,
        "win32com": False,
        "comtypes": False,
        "docx2pdf": False,
    }

    result["libreoffice"] = find_libreoffice() is not None

    if sys.platform == 'win32':
        try:
            import win32com.client
            result["win32com"] = True
        except ImportError:
            pass

        try:
            import comtypes.client
            result["comtypes"] = True
        except ImportError:
            pass

    try:
        import docx2pdf
        result["docx2pdf"] = True
    except ImportError:
        pass

    logger.info(f"Available PDF converters: {result}")
    return result


def get_install_instructions() -> str:
    if sys.platform == 'win32':
        return (
            "Install one of:\n"
            "  pip install pywin32\n"
            "  pip install docx2pdf\n"
            "  pip install comtypes\n"
            "  Or install LibreOffice"
        )
    elif sys.platform == 'darwin':
        return (
            "Install one of:\n"
            "  pip install docx2pdf (requires MS Word)\n"
            "  brew install --cask libreoffice"
        )
    else:
        return "sudo apt install libreoffice"


def find_libreoffice() -> str | None:
    for name in ("libreoffice", "soffice"):
        path = shutil.which(name)
        if path:
            return path

    if sys.platform == 'win32':
        candidates = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        ]
        for pf in [os.environ.get("ProgramFiles", ""),
                    os.environ.get("ProgramFiles(x86)", "")]:
            if pf:
                lo = os.path.join(pf, "LibreOffice", "program",
                                  "soffice.exe")
                if lo not in candidates:
                    candidates.append(lo)
        for path in candidates:
            if os.path.isfile(path):
                return path

    if sys.platform == 'darwin':
        mac = "/Applications/LibreOffice.app/Contents/MacOS/soffice"
        if os.path.isfile(mac):
            return mac

    return None


def convert_with_libreoffice(docx_path: str,
                             output_dir: str,
                             timeout: int = 300) -> str | None:
    lo_path = find_libreoffice()
    if not lo_path:
        return None

    effective_timeout = _compute_timeout(docx_path, timeout)

    try:
        cmd = [
            lo_path, '--headless', '--norestore',
            '--convert-to', 'pdf',
            '--outdir', output_dir,
            os.path.abspath(docx_path)
        ]
        creationflags = 0
        if sys.platform == 'win32':
            creationflags = subprocess.CREATE_NO_WINDOW

        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=effective_timeout, cwd=output_dir,
            creationflags=creationflags
        )

        if result.returncode == 0:
            base = os.path.splitext(os.path.basename(docx_path))[0]
            pdf_path = os.path.join(output_dir, f"{base}.pdf")
            if os.path.isfile(pdf_path):
                return pdf_path

        logger.error(f"LibreOffice rc={result.returncode}")
        return None

    except subprocess.TimeoutExpired:
        logger.error(f"LibreOffice: timeout {effective_timeout}s")
    except Exception as e:
        logger.error(f"LibreOffice error: {e}")
    return None


def convert_with_win32com(docx_path: str) -> str | None:
    if sys.platform != 'win32':
        return None
    try:
        import win32com.client
        import pythoncom
    except ImportError:
        return None

    word = None
    try:
        pythoncom.CoInitialize()
        word = win32com.client.Dispatch('Word.Application')
        word.Visible = False
        word.DisplayAlerts = False

        abs_path = os.path.abspath(docx_path)
        pdf_path = os.path.splitext(abs_path)[0] + '.pdf'

        doc = word.Documents.Open(abs_path)
        doc.SaveAs(pdf_path, FileFormat=17)
        doc.Close(False)

        if os.path.isfile(pdf_path):
            return pdf_path
        return None

    except Exception as e:
        logger.error(f"win32com error: {e}")
        return None
    finally:
        if word:
            try:
                word.Quit()
            except Exception:
                pass
        try:
            pythoncom.CoUninitialize()
        except Exception:
            pass


def convert_with_comtypes(docx_path: str) -> str | None:
    if sys.platform != 'win32':
        return None
    try:
        import comtypes.client
    except ImportError:
        return None

    word = None
    try:
        word = comtypes.client.CreateObject('Word.Application')
        word.Visible = False

        abs_path = os.path.abspath(docx_path)
        pdf_path = os.path.splitext(abs_path)[0] + '.pdf'

        doc = word.Documents.Open(abs_path)
        doc.SaveAs(pdf_path, FileFormat=17)
        doc.Close()

        if os.path.isfile(pdf_path):
            return pdf_path
        return None

    except Exception as e:
        logger.error(f"comtypes error: {e}")
        return None
    finally:
        if word:
            try:
                word.Quit()
            except Exception:
                pass


def convert_with_docx2pdf(docx_path: str) -> str | None:
    try:
        from docx2pdf import convert
    except ImportError:
        return None

    try:
        abs_path = os.path.abspath(docx_path)
        pdf_path = os.path.splitext(abs_path)[0] + '.pdf'
        convert(abs_path, pdf_path)
        if os.path.isfile(pdf_path):
            return pdf_path
        return None
    except Exception as e:
        logger.error(f"docx2pdf error: {e}")
        return None


def convert_docx_to_pdf(docx_path: str,
                        log_func=None,
                        timeout: int = 300) -> tuple[bool, str]:
    if log_func is None:
        log_func = lambda msg: None

    if not os.path.isfile(docx_path):
        return False, f"File not found: {docx_path}"

    output_dir = os.path.dirname(os.path.abspath(docx_path))

    effective_timeout = _compute_timeout(docx_path, timeout)
    size_mb = os.path.getsize(docx_path) / (1024 * 1024)
    log_func(f"  File size: {size_mb:.1f} MB, timeout: {effective_timeout}s")

    converters = [
        ("LibreOffice",
         lambda: convert_with_libreoffice(docx_path, output_dir, effective_timeout)),
        ("MS Word (win32com)",
         lambda: convert_with_win32com(docx_path)),
        ("MS Word (comtypes)",
         lambda: convert_with_comtypes(docx_path)),
        ("docx2pdf",
         lambda: convert_with_docx2pdf(docx_path)),
    ]

    errors = []
    for name, converter_func in converters:
        log_func(f"  Trying: {name}\u2026")
        try:
            pdf_path = converter_func()
            if pdf_path and os.path.isfile(pdf_path):
                return True, pdf_path
            else:
                errors.append(f"{name}: no result")
        except Exception as e:
            errors.append(f"{name}: {e}")

    instructions = get_install_instructions()
    error_details = "\n".join(f"  \u2022 {e}" for e in errors)
    error_msg = (
        f"No PDF converter available.\n\n"
        f"Tried:\n{error_details}\n\n"
        f"{instructions}"
    )
    return False, error_msg