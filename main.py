# main.py
from scripts.extract import extract_all
from scripts.transform import transform_all
from scripts.load import load_all

def main():
    raw = extract_all()
    transformed = transform_all(raw)
    load_all(transformed)

if __name__ == "__main__":
    main()