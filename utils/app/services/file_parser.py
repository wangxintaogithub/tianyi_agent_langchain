"""
文件解析器 - 支持 PDF、DOCX、Excel、CSV、纯文本
"""
import io
import csv
from pathlib import Path
from typing import BinaryIO


def parse_file(file: BinaryIO, filename: str) -> str:
    """根据文件扩展名自动选择解析方式，返回文本内容"""
    ext = Path(filename).suffix.lower()

    if ext == ".pdf":
        return _parse_pdf(file)
    elif ext in (".docx", ".doc"):
        return _parse_docx(file)
    elif ext in (".xlsx", ".xls"):
        return _parse_excel(file)
    elif ext == ".csv":
        return _parse_csv(file)
    elif ext in (".txt", ".md", ".json", ".xml", ".yaml", ".yml", ".log"):
        return _parse_text(file)
    elif ext in (".py", ".js", ".ts", ".java", ".cpp", ".c", ".h", ".go", ".rs", ".sh", ".bat"):
        return _parse_text(file)
    else:
        return f"[不支持的文件格式: {ext}，仅返回文件名]\n文件名: {filename}"


def _parse_pdf(file: BinaryIO) -> str:
    """解析 PDF 文件"""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=file.read(), filetype="pdf")
        lines = []
        for page in doc:
            lines.append(page.get_text())
        doc.close()
        return "\n".join(lines)
    except ImportError:
        return "需要安装 PyMuPDF: pip install pymupdf"
    except Exception as e:
        return f"PDF 解析失败: {e}"


def _parse_docx(file: BinaryIO) -> str:
    """解析 DOCX 文件"""
    try:
        from docx import Document
        doc = Document(file)
        lines = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(lines)
    except ImportError:
        return "需要安装 python-docx: pip install python-docx"
    except Exception as e:
        return f"DOCX 解析失败: {e}"


def _parse_excel(file: BinaryIO) -> str:
    """解析 Excel 文件"""
    try:
        import openpyxl
        wb = openpyxl.load_workbook(file, read_only=True, data_only=True)
        lines = []
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            lines.append(f"【工作表: {sheet_name}】")
            for row in ws.iter_row(values_only=True):
                row_str = " | ".join(str(cell) if cell is not None else "" for cell in row)
                if row_str.strip():
                    lines.append(row_str)
        return "\n".join(lines)
    except ImportError:
        return "需要安装 openpyxl: pip install openpyxl"
    except Exception as e:
        return f"Excel 解析失败: {e}"


def _parse_csv(file: BinaryIO) -> str:
    """解析 CSV 文件"""
    try:
        content = file.read().decode("utf-8-sig")
        reader = csv.reader(io.StringIO(content))
        lines = [" | ".join(row) for row in reader]
        return "\n".join(lines)
    except Exception as e:
        return f"CSV 解析失败: {e}"


def _parse_text(file: BinaryIO) -> str:
    """解析纯文本文件"""
    try:
        return file.read().decode("utf-8")
    except UnicodeDecodeError:
        try:
            file.seek(0)
            return file.read().decode("gbk")
        except Exception as e:
            return f"文本解析失败: {e}"
