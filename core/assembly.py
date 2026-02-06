import os
from jinja2 import Environment, FileSystemLoader

try:
    from weasyprint import HTML, CSS
    WEASY_AVAILABLE = True
except Exception as e:
    print(f"WARNING: WeasyPrint not available ({e}). PDF generation disabled.")
    WEASY_AVAILABLE = False

class Assembler:
    def __init__(self, template_dir: str = "templates"):
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def render_html(self, content: str, title: str, style: str = "pro") -> str:
        """
        Renders content into HTML using the specified style template.
        """
        template_name = f"theme_{style}.html"
        try:
            template = self.env.get_template(template_name)
        except:
             print(f"Template {template_name} not found, falling back to base.")
             return f"<h1>{title}</h1><div class='content'>{content}</div>"

        # Simple markdown to html conversion for the body content is needed if content is still markdown.
        # But commonly we might want to use a markdown library here.
        import markdown
        html_content = markdown.markdown(content)
        
        return template.render(
            title=title,
            content=html_content,
            style=style
        )

    def generate_pdf(self, html_content: str, output_path: str):
        """
        Converts HTML string to PDF file.
        """
        if not WEASY_AVAILABLE:
            print("PDF Generation skipped (WeasyPrint missing). Creating placeholder.")
            # Create a dummy text file renamed as PDF so the link works
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(f"PDF Generation is disabled because WeasyPrint (GTK3) is missing.\n\nRaw Content:\n{html_content}")
            return output_path
            
        HTML(string=html_content, base_url=".").write_pdf(output_path)
        return output_path

if __name__ == "__main__":
    # Test
    assembler = Assembler()
    # html = assembler.render_html("# Hello\n\nWorld", "Test Doc", "kids")
    # assembler.generate_pdf(html, "test.pdf")
    pass
