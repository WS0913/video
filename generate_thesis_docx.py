"""
生成毕业设计论文 Word 文档 - 优化版
支持：
1. 上标引用
2. 自动生成真实Word表格
3. 表格文字水平+垂直居中
4. 固定行高
5. 表头灰底
"""

import re
from docx import Document
from docx.shared import Pt, Cm, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml


def set_chinese_font(run, font_name='宋体'):
    """设置中文字体"""
    run.font.name = font_name
    run._element.rPr.rFonts.set(qn('w:eastAsia'), font_name)


def add_title(doc, text):
    para = doc.add_paragraph()
    run = para.add_run(text)

    run.font.size = Pt(18)
    run.font.bold = True
    set_chinese_font(run, '黑体')

    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para.paragraph_format.space_after = Pt(12)

    return para


def add_section_title(doc, text, is_center=True):
    para = doc.add_paragraph()

    run = para.add_run(text)
    run.font.size = Pt(16)
    run.font.bold = True
    set_chinese_font(run, '黑体')

    if is_center:
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER

    para.paragraph_format.space_before = Pt(12)
    para.paragraph_format.space_after = Pt(8)

    return para


def add_chapter_title(doc, text):
    para = doc.add_paragraph()

    run = para.add_run(text)
    run.font.size = Pt(16)
    run.font.bold = True
    set_chinese_font(run, '黑体')

    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para.paragraph_format.space_before = Pt(12)
    para.paragraph_format.space_after = Pt(8)

    return para


def add_heading_level1(doc, text):
    para = doc.add_paragraph()

    run = para.add_run(text)
    run.font.size = Pt(14)
    set_chinese_font(run, '黑体')

    para.paragraph_format.space_before = Pt(12)
    para.paragraph_format.space_after = Pt(8)

    return para


def add_heading_level2(doc, text):
    para = doc.add_paragraph()

    run = para.add_run(text)
    run.font.size = Pt(13)
    set_chinese_font(run, '黑体')

    para.paragraph_format.space_before = Pt(8)
    para.paragraph_format.space_after = Pt(6)

    return para


def add_citation_run(para, text):
    """处理 [数字] 为上标"""

    parts = re.split(r'(\[\d+\](?:\[\d+\])*)', text)

    for part in parts:

        if not part:
            continue

        if re.match(r'^\[\d+\]', part):

            run = para.add_run(part)
            run.font.size = Pt(10.5)
            run.font.superscript = True
            set_chinese_font(run, '宋体')

        else:

            run = para.add_run(part)
            run.font.size = Pt(12)
            set_chinese_font(run, '宋体')


def add_normal_paragraph(doc, text):
    """普通段落"""

    para = doc.add_paragraph()

    add_citation_run(para, text)

    para.paragraph_format.line_spacing = Pt(20)
    para.paragraph_format.first_line_indent = Cm(1)

    return para


def add_keywords(doc, text):
    para = doc.add_paragraph()

    run1 = para.add_run('关键词：')
    run1.font.size = Pt(12)
    run1.font.bold = True
    set_chinese_font(run1, '黑体')

    run2 = para.add_run(text)
    run2.font.size = Pt(12)
    set_chinese_font(run2, '宋体')

    para.paragraph_format.line_spacing = Pt(20)

    return para


def add_table_title(doc, text):
    para = doc.add_paragraph()

    run = para.add_run(text)
    run.font.size = Pt(10.5)
    set_chinese_font(run, '黑体')

    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para.paragraph_format.space_after = Pt(8)

    return para


# ==================== 真实表格生成 ====================

def create_real_table(doc, title, table_lines):
    """将 - 分隔的数据转换为真实Word表格"""

    if not table_lines:
        return

    add_table_title(doc, title)

    # 解析表头
    headers = [h.strip() for h in table_lines[0].split('-')]

    # 解析数据
    data = []

    for line in table_lines[1:]:

        if line.strip():
            row = [cell.strip() for cell in line.split('-')]
            data.append(row)

    # 创建表格
    table = doc.add_table(rows=len(data) + 1, cols=len(headers))
    table.style = 'Table Grid'

    # ==================== 固定行高 ====================

    for row in table.rows:
        row.height = Cm(0.8)

    # ==================== 表头 ====================

    for j, header in enumerate(headers):

        cell = table.cell(0, j)

        cell.text = header

        run = cell.paragraphs[0].runs[0]

        run.font.bold = True
        run.font.size = Pt(10.5)

        set_chinese_font(run, '黑体')

        # 水平居中
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

        # 垂直居中
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

        # 灰色表头背景
        shading_elm = parse_xml(
            r'<w:shd {} w:fill="D9D9D9"/>'.format(nsdecls('w'))
        )

        cell._tc.get_or_add_tcPr().append(shading_elm)

    # ==================== 数据 ====================

    for i, row in enumerate(data):

        for j, text in enumerate(row):

            if j < len(headers):

                cell = table.cell(i + 1, j)

                cell.text = text

                run = cell.paragraphs[0].runs[0]

                run.font.size = Pt(10)

                set_chinese_font(run, '宋体')

                # 水平居中
                cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

                # 垂直居中
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

    # ==================== 设置列宽 ====================

    for column in table.columns:

        for cell in column.cells:
            cell.width = Inches(2.0)

    # 表格后空行
    doc.add_paragraph()


def add_figure_placeholder(doc, text):

    for _ in range(8):
        doc.add_paragraph()

    para = doc.add_paragraph()

    run = para.add_run(text)
    run.font.size = Pt(10.5)

    set_chinese_font(run, '黑体')

    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para.paragraph_format.space_after = Pt(6)

    return para


def add_reference(doc, text):

    para = doc.add_paragraph()

    run = para.add_run(text)

    run.font.size = Pt(10.5)

    set_chinese_font(run, '宋体')

    para.paragraph_format.line_spacing = Pt(18)

    para.paragraph_format.first_line_indent = Cm(-0.5)
    para.paragraph_format.left_indent = Cm(0.5)

    return para


def main():

    print("=" * 70)
    print("开始生成毕业设计论文 Word 文档（最终优化版）")
    print("=" * 70)

    try:

        with open('毕业设计论文.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()

    except FileNotFoundError:

        print("错误：找不到 毕业设计论文.txt 文件")
        return

    doc = Document()

    # ==================== 页面设置 ====================

    section = doc.sections[0]

    section.page_height = Cm(29.7)
    section.page_width = Cm(21)

    section.left_margin = Cm(3)
    section.right_margin = Cm(2.5)

    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)

    i = 0

    while i < len(lines):

        line = lines[i].strip()

        if not line:
            i += 1
            continue

        # ==================== 标题 ====================

        if i == 0 and line.startswith('题目名称：'):

            title_text = line.replace('题目名称：', '').strip()

            add_title(doc, title_text)

            doc.add_paragraph()

            i += 1
            continue

        # ==================== 摘要 ====================

        if line == '摘  要' or line == 'Abstract':

            add_section_title(doc, line)

            doc.add_paragraph()

            i += 1
            continue

        # ==================== 中文关键词 ====================

        if line.startswith('关键词：'):

            add_keywords(doc, line.replace('关键词：', '').strip())

            i += 1
            continue

        # ==================== 英文关键词 ====================

        if line.startswith('Keywords:'):

            para = doc.add_paragraph()

            run1 = para.add_run('Keywords: ')
            run1.font.size = Pt(12)
            run1.font.bold = True
            run1.font.name = 'Times New Roman'

            run2 = para.add_run(
                line.replace('Keywords:', '').strip()
            )

            run2.font.size = Pt(12)
            run2.font.name = 'Times New Roman'

            para.paragraph_format.line_spacing = Pt(20)

            i += 1
            continue

        # ==================== 章节 ====================

        if re.match(r'^第\d+章\s+', line):

            doc.add_page_break()

            add_chapter_title(doc, line)

            doc.add_paragraph()

            i += 1
            continue

        # ==================== 一级标题 ====================

        if re.match(r'^\d+\.\d+\s+', line) and not re.match(r'^\d+\.\d+\.\d+', line):

            add_heading_level1(doc, line)

            i += 1
            continue

        # ==================== 二级标题 ====================

        if re.match(r'^\d+\.\d+\.\d+\s+', line):

            add_heading_level2(doc, line)

            i += 1
            continue

        # ==================== 表格 ====================

        if re.match(r'^表\d+-\d+', line):

            table_title = line

            i += 1

            table_lines = []

            while i < len(lines):

                next_line = lines[i].strip()

                if (
                    not next_line
                    or re.match(
                        r'^(第\d+章|\d+\.\d+|表\d+-\d+|【图|参考文献|附  录|致  谢)',
                        next_line
                    )
                ):
                    break

                table_lines.append(next_line)

                i += 1

            create_real_table(doc, table_title, table_lines)

            continue

        # ==================== 图片占位 ====================

        if re.match(r'^【图', line):

            figure_text = (
                line.replace('【', '')
                .replace('】', '')
                .replace('插入位置', '')
                .strip()
            )

            add_figure_placeholder(doc, figure_text)

            i += 1
            continue

        # ==================== 特殊章节 ====================

        if line in ['参考文献', '附  录', '致  谢']:

            doc.add_page_break()

            add_section_title(doc, line, is_center=True)

            doc.add_paragraph()

            i += 1
            continue

        # ==================== 参考文献 ====================

        if re.match(r'^\[\d+\]', line):

            add_reference(doc, line)

            i += 1
            continue

        # ==================== 普通段落 ====================

        add_normal_paragraph(doc, line)

        i += 1

    # ==================== 保存 ====================

    output_file = '毕业设计论文.docx'

    doc.save(output_file)

    print(f"✓ Word 文档已生成：{output_file}")
    print("✓ 已支持：")
    print("  1. 上标引用")
    print("  2. 真实Word表格")
    print("  3. 表格水平+垂直居中")
    print("  4. 固定行高")
    print("  5. 表头灰底")


if __name__ == '__main__':
    main()