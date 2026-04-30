import os
import json
def add_overlays_to_document(doc_json_path):
    with open(doc_json_path, 'r', encoding='utf-8') as f:
        doc = json.load(f)
    doc_id = doc.get('doc_id')
    if not doc_id:
        print(f"No doc_id in {doc_json_path}")
        return
    # Buscar imágenes de overlays
    overlay_dir = os.path.join('data', 'cache', doc_id, 'overlays')
    if not os.path.exists(overlay_dir):
        print(f"No overlay dir for {doc_id}")
        return
    overlays = []
    for fname in sorted(os.listdir(overlay_dir)):
        if fname.lower().endswith(('.png', '.jpg', '.jpeg')):
            # Extraer número de página del nombre (ej: overlay_p3.png)
            parts = fname.split('p')
            if len(parts) > 1 and parts[-1].split('.')[0].isdigit():
                page_number = int(parts[-1].split('.')[0])
            else:
                continue
            overlays.append({
                'page_number': page_number,
                'path': os.path.join('data', 'cache', doc_id, 'overlays', fname)
            })
    if overlays:
        doc['overlays'] = overlays
        with open(doc_json_path, 'w', encoding='utf-8') as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
        print(f"Updated overlays in {doc_json_path}")
    else:
        print(f"No overlays found for {doc_id}")

def process_all_documents():
    base = os.path.join('data', 'output')
    for doc_id in os.listdir(base):
        doc_folder = os.path.join(base, doc_id)
        doc_json = os.path.join(doc_folder, 'document.json')
        if os.path.exists(doc_json):
            add_overlays_to_document(doc_json)

if __name__ == '__main__':
    process_all_documents()
