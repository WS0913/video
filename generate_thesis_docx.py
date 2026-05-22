"""
生成毕业设计论文 Word 文档 - 方案一：基础版
包含所有文字内容和基本格式，表格和图表需要手动调整
"""
import re
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn

def set_chinese_font(run, font_name='宋体'):
    """设置中文字体"""
    run.font.name = font_name
    run._element.rPr.rFonts.set(qn('w:eastAsia'), font_name)

def add_title(doc, text):
    """添加论文标题"""
    para = doc.add_paragraph()
    run = para.add_run(text)
    run.font.size = Pt(18)
    run.font.bold = True
    set_chinese_font(run, '黑体')
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para.paragraph_format.space_after = Pt(12)
    return para

def add_section_title(doc, text, is_center=True):
    """添加章节标题（摘要、Abstract等）"""
    para = doc.add_paragraph()
    run = para.add_run(text)
    run.font.size = Pt(14)
    run.font.bold = True
    set_chinese_font(run, '黑体')
    if is_center:
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para.paragraph_format.space_before = Pt(12)
    para.paragraph_format.space_after = Pt(8)
    return para

def add_chapter_title(doc, text):
    """添加章标题（第X章）"""
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
    """添加一级标题（X.X）"""
    para = doc.add_paragraph()
    run = para.add_run(text)
    run.font.size = Pt(14)
    run.font.bold = True
    set_chinese_font(run, '黑体')
    para.paragraph_format.space_before = Pt(12)
    para.paragraph_format.space_after = Pt(8)
    return para

def add_heading_level2(doc, text):
    """添加二级标题（X.X.X）"""
    para = doc.add_paragraph()
    run = para.add_run(text)
    run.font.size = Pt(13)
    run.font.bold = True
    set_chinese_font(run, '黑体')
    para.paragraph_format.space_before = Pt(8)
    para.paragraph_format.space_after = Pt(6)
    return para

def add_normal_paragraph(doc, text, first_line_indent=True):
    """添加正文段落"""
    para = doc.add_paragraph()
    run = para.add_run(text)
    run.font.size = Pt(12)
    set_chinese_font(run, '宋体')
    para.paragraph_format.line_spacing = Pt(20)
    if first_line_indent:
        para.paragraph_format.first_line_indent = Cm(1)
    return para

def add_keywords(doc, text):
    """添加关键词"""
    para = doc.add_paragraph()
    # 关键词标签
    run1 = para.add_run('关键词：')
    run1.font.size = Pt(12)
    run1.font.bold = True
    set_chinese_font(run1, '黑体')
    # 关键词内容
    run2 = para.add_run(text)
    run2.font.size = Pt(12)
    set_chinese_font(run2, '宋体')
    para.paragraph_format.line_spacing = Pt(20)
    return para

def add_table_title(doc, text):
    """添加表格标题"""
    para = doc.add_paragraph()
    run = para.add_run(text)
    run.font.size = Pt(10.5)
    run.font.bold = True
    set_chinese_font(run, '黑体')
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para.paragraph_format.space_before = Pt(6)
    para.paragraph_format.space_after = Pt(6)
    return para

def add_figure_placeholder(doc, text):
    """添加图片占位符"""
    para = doc.add_paragraph()
    run = para.add_run(text)
    run.font.size = Pt(10.5)
    set_chinese_font(run, '宋体')
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para.paragraph_format.space_before = Pt(6)
    para.paragraph_format.space_after = Pt(6)
    return para

def add_reference(doc, text):
    """添加参考文献条目"""
    para = doc.add_paragraph()
    run = para.add_run(text)
    run.font.size = Pt(10.5)
    set_chinese_font(run, '宋体')
    para.paragraph_format.line_spacing = Pt(18)
    para.paragraph_format.first_line_indent = Cm(-0.5)
    para.paragraph_format.left_indent = Cm(0.5)
    return para

def main():
    print("=" * 60)
    print("开始生成毕业设计论文 Word 文档（方案一：基础版）")
    print("=" * 60)

    # 读取论文内容
    try:
        with open('毕业设计论文.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print("错误：找不到 毕业设计论文.txt 文件")
        return

    # 创建文档
    doc = Document()

    # 设置页面
    section = doc.sections[0]
    section.page_height = Cm(29.7)  # A4
    section.page_width = Cm(21)
    section.left_margin = Cm(3)
    section.right_margin = Cm(2.5)
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)

    print("正在处理论文内容...")

    # 逐行处理
    i = 0
    total_lines = len(lines)

    while i < total_lines:
        line = lines[i].strip()

        if not line:
            i += 1
            continue

        # 跳过第一行标题（已经单独处理）
        if i == 0 and line.startswith('题目名称：'):
            title_text = line.replace('题目名称：', '').strip()
            add_title(doc, title_text)
            doc.add_paragraph()  # 空行
            i += 1
            continue

        # 检测摘要
        if line == '摘  要':
            add_section_title(doc, line)
            doc.add_paragraph()  # 空行
            i += 1
            continue

        # 检测Abstract
        if line == 'Abstract':
            add_section_title(doc, line)
            doc.add_paragraph()  # 空行
            i += 1
            continue

        # 检测关键词
        if line.startswith('关键词：'):
            keywords_text = line.replace('关键词：', '').strip()
            add_keywords(doc, keywords_text)
            i += 1
            continue

        # 检测Keywords
        if line.startswith('Keywords:'):
            para = doc.add_paragraph()
            run1 = para.add_run('Keywords: ')
            run1.font.size = Pt(12)
            run1.font.bold = True
            run1.font.name = 'Times New Roman'
            run2 = para.add_run(line.replace('Keywords:', '').strip())
            run2.font.size = Pt(12)
            run2.font.name = 'Times New Roman'
            para.paragraph_format.line_spacing = Pt(20)
            i += 1
            continue

        # 检测章标题（第X章）
        if re.match(r'^第\d+章\s+', line):
            doc.add_page_break()  # 新章节另起一页
            add_chapter_title(doc, line)
            doc.add_paragraph()  # 空行
            i += 1
            continue

        # 检测一级标题（X.X）
        if re.match(r'^\d+\.\d+\s+', line) and not re.match(r'^\d+\.\d+\.\d+', line):
            add_heading_level1(doc, line)
            i += 1
            continue

        # 检测二级标题（X.X.X）
        if re.match(r'^\d+\.\d+\.\d+\s+', line):
            add_heading_level2(doc, line)
            i += 1
            continue

        # 检测表格标题
        if re.match(r'^表\d+-\d+', line):
            add_table_title(doc, line)
            # 读取表格内容（空格对齐的纯文本）
            i += 1
            table_lines = []
            while i < total_lines:
                next_line = lines[i].strip()
                # 如果遇到空行或新的标题，表格结束
                if not next_line or re.match(r'^(第\d+章|\d+\.\d+|表\d+-\d+|【图)', next_line):
                    break
                table_lines.append(next_line)
                i += 1

            # 添加表格内容为预格式化文本（保持空格对齐）
            if table_lines:
                para = doc.add_paragraph()
                run = para.add_run('\n'.join(table_lines))
                run.font.size = Pt(10.5)
                run.font.name = 'Courier New'  # 使用等宽字体保持对齐
                set_chinese_font(run, '宋体')
                para.paragraph_format.line_spacing = Pt(16)
            continue

        # 检测图片占位符
        if re.match(r'^【图\d+-\d+', line):
            add_figure_placeholder(doc, line)
            i += 1
            continue

        # 检测参考文献标题
        if line == '参考文献':
            doc.add_page_break()
            add_section_title(doc, line, is_center=True)
            doc.add_paragraph()  # 空行
            i += 1
            continue

        # 检测参考文献条目
        if re.match(r'^\[\d+\]', line):
            add_reference(doc, line)
            i += 1
            continue

        # 检测附录标题
        if line == '附  录':
            doc.add_page_break()
            add_section_title(doc, line, is_center=True)
            doc.add_paragraph()  # 空行
            i += 1
            continue

        # 检测致谢标题
        if line == '致  谢':
            doc.add_page_break()
            add_section_title(doc, line, is_center=True)
            doc.add_paragraph()  # 空行
            i += 1
            continue

        # 普通段落
        add_normal_paragraph(doc, line)
        i += 1

    # 保存文档
    output_file = '毕业设计论文.docx'
    doc.save(output_file)

    print("=" * 60)
    print(f"✓ Word 文档已生成：{output_file}")
    print("=" * 60)
    print("\n后续步骤：")
    print("1. 打开生成的 Word 文档")
    print("2. 表格已保留空格对齐格式，可以：")
    print("   - 选中表格内容")
    print("   - 点击【插入】→【表格】→【文本转换成表格】")
    print("   - 选择【空格】作为分隔符")
    print("3. 从 论文图表汇总.html 中截取图表并插入到对应位置")
    print("4. 使用格式刷统一调整格式细节")
    print("=" * 60)

if __name__ == '__main__':
    main()
