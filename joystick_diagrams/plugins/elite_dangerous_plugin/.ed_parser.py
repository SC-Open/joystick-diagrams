import argparse
import json
from xml.etree import ElementTree


def parse_elite_dangerous_binds(file_path):
    tree = ElementTree.parse(file_path)
    root = tree.getroot()

    binds = {}
    for child in root:
        if child.attrib:
            binds[child.tag] = child.attrib
        else:
            binds[child.tag] = child.text

    return binds

def main():
    parser = argparse.ArgumentParser(description='Parse Elite Dangerous binds.')
    parser.add_argument('file_path', type=str, help='The path to the binds file.')

    args = parser.parse_args()

    binds = parse_elite_dangerous_binds(args.file_path)
    print(json.dumps(binds, indent=4))

if __name__ == '__main__':
    main()
