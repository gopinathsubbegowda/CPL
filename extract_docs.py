import os
import zipfile
import xml.etree.ElementTree as ET

def docx_to_txt(docx_path):
    try:
        with zipfile.ZipFile(docx_path) as docx:
            xml_content = docx.read('word/document.xml')
            root = ET.fromstring(xml_content)
            
            # Namespaces
            ns = {
                'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
            }
            
            paragraphs = []
            for paragraph in root.iter('{' + ns['w'] + '}p'):
                texts = [node.text for node in paragraph.iter('{' + ns['w'] + '}t') if node.text]
                if texts:
                    paragraphs.append(''.join(texts))
            return '\n\n'.join(paragraphs)
    except Exception as e:
        return f"Error reading {docx_path}: {e}"

def odt_to_txt(odt_path):
    try:
        with zipfile.ZipFile(odt_path) as odt:
            xml_content = odt.read('content.xml')
            root = ET.fromstring(xml_content)
            
            paragraphs = []
            # Gather text from text elements
            for elem in root.iter():
                # Elements containing text in ODF
                tag_local = elem.tag.split('}')[-1]
                if tag_local in ('p', 'h', 'section', 'span'):
                    # ODT text element
                    # We can iterate through the text
                    text = "".join(elem.itertext()).strip()
                    if text and tag_local in ('p', 'h'):
                        paragraphs.append(text)
            return '\n\n'.join(paragraphs)
    except Exception as e:
        return f"Error reading {odt_path}: {e}"

def main():
    workspace = "/home/gopinath/Documents/CPL"
    for filename in os.listdir(workspace):
        filepath = os.path.join(workspace, filename)
        if filename.endswith(".docx"):
            print(f"Converting {filename}...")
            text = docx_to_txt(filepath)
            out_filename = filename.rsplit(".", 1)[0] + ".md"
            out_filepath = os.path.join(workspace, out_filename)
            with open(out_filepath, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"Saved to {out_filename}")
        elif filename.endswith(".odt"):
            print(f"Converting {filename}...")
            text = odt_to_txt(filepath)
            out_filename = filename.rsplit(".", 1)[0] + ".md"
            out_filepath = os.path.join(workspace, out_filename)
            with open(out_filepath, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"Saved to {out_filename}")

if __name__ == "__main__":
    main()
