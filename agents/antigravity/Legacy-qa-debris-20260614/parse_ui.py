import xml.etree.ElementTree as ET
import sys

def parse_node(node, depth=0):
    text = node.get('text')
    resource_id = node.get('resource-id')
    bounds = node.get('bounds')
    if text or resource_id:
        print(f"{'  ' * depth}Text: {text}, ID: {resource_id}, Bounds: {bounds}")
    for child in node:
        parse_node(child, depth + 1)

try:
    tree = ET.parse('agents/antigravity/view.xml')
    root = tree.getroot()
    parse_node(root)
except Exception as e:
    print(e)
