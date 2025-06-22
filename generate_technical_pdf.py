#!/usr/bin/env python3
"""
Generador de PDF para la Guía Técnica RT-11
Convierte el documento Markdown a un PDF profesional con formato técnico
"""

import os
import sys
from pathlib import Path
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, blue, red, gray
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from reportlab.platypus.frames import Frame
from reportlab.lib import colors
from reportlab.pdfgen import canvas
import re
from datetime import datetime

class RT11TechnicalGuide:
    def __init__(self):
        self.doc_elements = []
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
        
    def setup_custom_styles(self):
        """Configurar estilos personalizados para el documento"""
        
        # Estilo para el título principal
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            textColor=HexColor('#1f4e79'),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Estilo para subtítulos principales (H1)
        self.styles.add(ParagraphStyle(
            name='Heading1Custom',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=20,
            spaceBefore=30,
            textColor=HexColor('#2e5090'),
            fontName='Helvetica-Bold',
            borderWidth=1,
            borderColor=HexColor('#2e5090'),
            borderPadding=10,
            backColor=HexColor('#f0f4f8')
        ))
        
        # Estilo para subtítulos secundarios (H2)
        self.styles.add(ParagraphStyle(
            name='Heading2Custom',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=15,
            spaceBefore=20,
            textColor=HexColor('#1f4e79'),
            fontName='Helvetica-Bold'
        ))
        
        # Estilo para subtítulos terciarios (H3)
        self.styles.add(ParagraphStyle(
            name='Heading3Custom',
            parent=self.styles['Heading3'],
            fontSize=12,
            spaceAfter=10,
            spaceBefore=15,
            textColor=HexColor('#1f4e79'),
            fontName='Helvetica-Bold'
        ))
        
        # Estilo para código
        self.styles.add(ParagraphStyle(
            name='CodeBlock',
            parent=self.styles['Code'],
            fontSize=9,
            fontName='Courier',
            leftIndent=20,
            rightIndent=20,
            spaceAfter=15,
            spaceBefore=10,
            backColor=HexColor('#f8f9fa'),
            borderWidth=1,
            borderColor=HexColor('#e9ecef'),
            borderPadding=10
        ))
        
        # Estilo para texto normal justificado
        self.styles.add(ParagraphStyle(
            name='BodyTextJustified',
            parent=self.styles['BodyText'],
            fontSize=11,
            spaceAfter=12,
            alignment=TA_JUSTIFY,
            fontName='Times-Roman'
        ))
        
        # Estilo para listas
        self.styles.add(ParagraphStyle(
            name='BulletList',
            parent=self.styles['BodyText'],
            fontSize=11,
            leftIndent=30,
            bulletIndent=15,
            spaceAfter=8,
            fontName='Times-Roman'
        ))
        
        # Estilo para texto de tabla
        self.styles.add(ParagraphStyle(
            name='TableText',
            parent=self.styles['BodyText'],
            fontSize=9,
            fontName='Times-Roman'
        ))
        
        # Estilo para pie de página
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['BodyText'],
            fontSize=9,
            alignment=TA_CENTER,
            textColor=gray,
            fontName='Times-Italic'
        ))

    def parse_markdown_content(self, content):
        """Parsea el contenido Markdown y lo convierte a elementos de reportlab"""
        lines = content.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                i += 1
                continue
                
            # Títulos
            if line.startswith('# '):
                if 'Guía Técnica Completa' in line:
                    # Título principal del documento
                    self.add_title_page(line[2:])
                else:
                    self.doc_elements.append(Paragraph(line[2:], self.styles['Heading1Custom']))
                    self.doc_elements.append(Spacer(1, 12))
                    
            elif line.startswith('## '):
                self.doc_elements.append(Paragraph(line[3:], self.styles['Heading2Custom']))
                self.doc_elements.append(Spacer(1, 8))
                
            elif line.startswith('### '):
                self.doc_elements.append(Paragraph(line[4:], self.styles['Heading3Custom']))
                self.doc_elements.append(Spacer(1, 6))
                
            # Tabla de contenidos
            elif line.startswith('## Tabla de Contenidos'):
                # Saltar la tabla de contenidos, la generaremos automáticamente
                while i < len(lines) and not lines[i].startswith('---'):
                    i += 1
                    
            # Bloques de código
            elif line.startswith('```'):
                i += 1
                code_lines = []
                while i < len(lines) and not lines[i].strip().startswith('```'):
                    code_lines.append(lines[i])
                    i += 1
                
                if code_lines:
                    code_text = '\n'.join(code_lines)
                    # Escape HTML characters
                    code_text = code_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    self.doc_elements.append(Paragraph(f'<pre>{code_text}</pre>', self.styles['CodeBlock']))
                    self.doc_elements.append(Spacer(1, 8))
                    
            # Tablas
            elif '|' in line and line.count('|') >= 2:
                table_data = []
                # Leer toda la tabla
                table_lines = []
                while i < len(lines) and '|' in lines[i]:
                    table_lines.append(lines[i])
                    i += 1
                i -= 1  # Retroceder uno porque el bucle principal incrementará
                
                # Procesar líneas de tabla
                for table_line in table_lines:
                    if table_line.strip().startswith('|---') or table_line.strip().startswith('|--'):
                        continue  # Saltar líneas de separación
                    
                    cells = [cell.strip() for cell in table_line.split('|')[1:-1]]
                    if cells:
                        # Convertir a objetos Paragraph para mejor formato
                        formatted_cells = [Paragraph(cell, self.styles['TableText']) for cell in cells]
                        table_data.append(formatted_cells)
                
                if table_data:
                    self.add_table(table_data)
                    
            # Listas con viñetas
            elif line.startswith('- '):
                self.doc_elements.append(Paragraph(f'• {line[2:]}', self.styles['BulletList']))
                
            # Líneas de separación
            elif line.startswith('---'):
                self.doc_elements.append(Spacer(1, 20))
                
            # Párrafos normales
            else:
                if line:  # Solo procesar líneas no vacías
                    # Procesar markdown básico
                    processed_line = self.process_inline_markdown(line)
                    self.doc_elements.append(Paragraph(processed_line, self.styles['BodyTextJustified']))
                    self.doc_elements.append(Spacer(1, 6))
            
            i += 1

    def process_inline_markdown(self, text):
        """Procesa markdown inline como **bold**, *italic*, `code`"""
        # Bold
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        # Italic
        text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
        # Code inline
        text = re.sub(r'`(.*?)`', r'<font name="Courier" size="10" color="#d63384">\1</font>', text)
        return text

    def add_title_page(self, title):
        """Agrega una página de título profesional"""
        # Logo DEC (texto estilizado)
        dec_logo = Paragraph(
            '<font name="Helvetica-Bold" size="24" color="#1f4e79">DEC</font>',
            ParagraphStyle('DECLogo', alignment=TA_CENTER)
        )
        self.doc_elements.append(Spacer(1, 2*inch))
        self.doc_elements.append(dec_logo)
        self.doc_elements.append(Spacer(1, 0.5*inch))
        
        # Título principal
        title_para = Paragraph(title, self.styles['CustomTitle'])
        self.doc_elements.append(title_para)
        self.doc_elements.append(Spacer(1, 0.3*inch))
        
        # Subtítulo
        subtitle = Paragraph(
            'Análisis Técnico Completo del Sistema de Archivos RT-11<br/>y Documentación del Extractor',
            ParagraphStyle('Subtitle', 
                         fontSize=14, 
                         alignment=TA_CENTER, 
                         textColor=HexColor('#666666'),
                         fontName='Times-Italic')
        )
        self.doc_elements.append(subtitle)
        self.doc_elements.append(Spacer(1, 1*inch))
        
        # Información del documento
        info_style = ParagraphStyle('InfoBox',
                                  fontSize=12,
                                  alignment=TA_CENTER,
                                  borderWidth=1,
                                  borderColor=HexColor('#cccccc'),
                                  borderPadding=20,
                                  backColor=HexColor('#f8f9fa'))
        
        info_text = f"""
        <b>Documento Técnico</b><br/>
        RT-11 Extractor Project<br/>
        <br/>
        <i>Preservación de Software Histórico</i><br/>
        Digital Equipment Corporation (DEC)<br/>
        PDP-11 / RT-11 Operating System<br/>
        <br/>
        Versión 1.0 - {datetime.now().strftime('%B %Y')}
        """
        
        info_para = Paragraph(info_text, info_style)
        self.doc_elements.append(info_para)
        self.doc_elements.append(Spacer(1, 1*inch))
        
        # Nota de preservación histórica
        preservation_text = """
        <i>"Este documento forma parte de un esfuerzo de preservación del software histórico,
        permitiendo el acceso a miles de programas desarrollados para las minicomputadoras
        PDP-11 de Digital Equipment Corporation entre 1970 y 1990."</i>
        """
        
        preservation_para = Paragraph(preservation_text, 
                                    ParagraphStyle('Preservation',
                                                 fontSize=10,
                                                 alignment=TA_CENTER,
                                                 textColor=HexColor('#666666'),
                                                 fontName='Times-Italic'))
        self.doc_elements.append(preservation_para)
        self.doc_elements.append(PageBreak())

    def add_table(self, table_data):
        """Agrega una tabla formateada al documento"""
        if not table_data:
            return
            
        # Crear la tabla
        table = Table(table_data)
        
        # Estilo de tabla simplificado
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2e5090')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f8f9fa')),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#dee2e6')),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ])
        
        table.setStyle(table_style)
        self.doc_elements.append(table)
        self.doc_elements.append(Spacer(1, 15))

    def generate_pdf(self, output_path):
        """Genera el PDF final"""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Leer el archivo markdown
        md_path = Path(__file__).parent / 'RT11_Technical_Guide.md'
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parsear contenido
        self.parse_markdown_content(content)
        
        # Agregar tabla de contenidos automática
        toc = TableOfContents()
        toc.levelStyles = [
            ParagraphStyle(fontSize=14, name='TOCHeading1', leftIndent=20, fontName='Times-Bold'),
            ParagraphStyle(fontSize=12, name='TOCHeading2', leftIndent=40, fontName='Times-Roman'),
            ParagraphStyle(fontSize=10, name='TOCHeading3', leftIndent=60, fontName='Times-Roman'),
        ]
        
        # Insertar TOC después de la página de título
        toc_title = Paragraph('Tabla de Contenidos', self.styles['Heading1Custom'])
        self.doc_elements.insert(0, toc_title)
        self.doc_elements.insert(1, Spacer(1, 12))
        self.doc_elements.insert(2, toc)
        self.doc_elements.insert(3, PageBreak())
        
        # Construir PDF
        doc.build(self.doc_elements)
        print(f"PDF generado exitosamente: {output_path}")

def main():
    """Función principal"""
    try:
        # Verificar dependencias
        try:
            from reportlab.lib.pagesizes import letter
        except ImportError:
            print("Error: reportlab no está instalado.")
            print("Instala con: pip install reportlab")
            return 1
        
        # Crear generador
        generator = RT11TechnicalGuide()
        
        # Generar PDF
        output_path = Path(__file__).parent / 'RT11_Technical_Guide.pdf'
        generator.generate_pdf(str(output_path))
        
        # Mostrar información
        print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    PDF GENERADO EXITOSAMENTE                                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Archivo: {output_path.name:<60} ║
║ Ubicación: {str(output_path.parent):<56} ║
║ Tamaño: {output_path.stat().st_size / 1024:.1f} KB{' ' * 55} ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Contenido del PDF:                                                          ║
║ • Página de título profesional con logo DEC                                 ║
║ • Tabla de contenidos automática                                            ║
║ • Documentación técnica completa de RT-11                                   ║
║ • Explicación detallada del proceso de extracción                           ║
║ • Ejemplos prácticos y casos de uso                                         ║
║ • Apéndices con tablas de referencia                                        ║
║ • Formato profesional con estilos técnicos                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """)
        
        return 0
        
    except Exception as e:
        print(f"Error generando PDF: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
